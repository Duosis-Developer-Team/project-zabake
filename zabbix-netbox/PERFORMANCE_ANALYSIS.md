# Performance Analysis - Device Processing Loop

## Optimization baseline (2026-05-22)

Measured from AWX job `109471` (764 monitor devices, sync_devices only):

| Metric | Before optimization |
|--------|---------------------|
| Total Ansible tasks | ~146,020 |
| Per-host task estimate | ~191 |
| HMDL bootstrap per device | 9 tasks x 1077 |
| template.get per host | 781 API calls |
| hostgroup.get/create per host | ~1562 API calls |
| Debug tasks (default on) | ~7,029 |

**Phase A payload builder** (2026): `parallel_compare_engine.py` + `zabbix_payload_builder.py` build ready `host.create` / `host.update` params in parallel. Phase B (`process_*_apply.yml`) only POSTs plan payloads and records results — no per-host Ansible mapping.

**Implemented mitigations** (see role `netbox_zabbix_sync`):

- `load_role_configuration.yml` — YAML mappings loaded once
- `bootstrap_hmdl_log.yml` — HMDL DDL once per run
- `fetch_all_zabbix_templates.yml` — single `template.get`
- `fetch_all_zabbix_hostgroups.yml` — single `hostgroup.get` + shared `zbx_group_map_global`
- `fetch_hmdl_baseline_bulk.yml` — one SQL for all device baselines
- `debug_mode: false` — suppress per-host debug tasks
- Two-phase sync: sequential compare (no Zabbix writes) + sequential apply (Zabbix writes); `async`/`poll`/`throttle` are invalid on `include_tasks`
- `ansible.cfg`: `profile_tasks` for post-run timing

**Target** (1000+ monitor devices, all sync flags): 30–90 minutes vs ~12 hours.

Re-run AWX with `callback_whitelist=profile_tasks` after deploy to capture after metrics.

---

## 🚀 Architecture v2: Parallel Compare Engine (2026-05-22)

### Problem (job 109487)
- **127 devices compare + apply: 47 minutes**, then fatal abort
- `zbx_templates_found_names` undefined error (self-reference in same `set_fact` block)
- Ansible `async`/`poll`/`throttle` invalid on `include_tasks` → forced sequential compare

### New Architecture

```
Bootstrap + prefetch (run_once)
    ↓
Phase A: parallel_compare_engine.py (ThreadPoolExecutor, 20 workers)
    Devices + Platforms + VFWs in parallel
    ↓
device_plan_*.json / platform_plan_*.json / vfw_plan_*.json
    ↓
Phase B: Ansible sequential apply (Zabbix host.create / host.update)
    process_device_apply.yml / process_platform_apply.yml / process_virtual_fw_apply.yml
    ↓
HMDL log (hmdl_sync_log.yml — existing audit infrastructure unchanged)
```

### Time Estimate (120 devices)

| Phase | Duration |
|-------|----------|
| Bootstrap + prefetch | ~30s (unchanged) |
| Phase A: Python parallel compare (20 workers) | **~60–120s** (vs. ~22 min before) |
| Phase B: Ansible sequential apply (~3–5s/host) | ~6–10 min |
| **Total** | **8–12 minutes** ✅ (target < 15 min) |

### Caveats

- **2643 hosts (full inventory)**: Apply phase remains sequential → ~3 hours. This is a separate feature
  requiring either sliced AWX jobs or a Python apply pool (ZBX-4134 trade-off).
- **Feature flag**: `use_python_parallel_compare: false` falls back to legacy single-phase Ansible loop
  (for rollback without code changes).
- **Error isolation**: A single item exception in the compare engine writes an error plan (action=skip)
  and does not abort the other items. Compare errors are surfaced in the AWX job log.

### Reliability fixes included (v2)

| Bug | Fix |
|-----|-----|
| `zbx_templates_found_names` undefined (job 109487) | Split into two separate `set_fact` tasks |
| Tab characters in hostnames (reliability D) | `sanitize_hostname()` in engine |
| Platform canonical-host collision (reliability E) | Canonical hostname override check in `compare_one_platform()` |

---

## 📊 Current Performance Issue

### Observed Metrics (job_597.txt)
- **17 devices** processed in **~90 seconds**
- **~5-6 seconds per device**
- **16 times** `Load mappings` task executed (should be 1 time)
- **~230 tasks per device** (most skipped)

### Root Cause Analysis

#### Problem: Entire Role Re-execution Per Device

Current architecture:
```
For each device in netbox_devices:
  ├─ Include zabbix_migration role (FULL EXECUTION)
  │  ├─ Load mappings (~40 tasks)
  │  ├─ Validate parameters (~50 tasks)  
  │  ├─ Check host existence (~30 tasks)
  │  ├─ Create/Update logic (~80 tasks)
  │  └─ Error handling (~30 tasks)
  └─ Total: ~230 tasks × skip overhead
```

**Why This Is Slow:**
1. **Ansible Task Overhead**: Each task has setup/teardown cost (~20-50ms)
2. **Repeated File I/O**: Mappings loaded 17 times (should be once)
3. **Conditional Evaluation**: 200+ `when:` conditions evaluated per device
4. **Role Include Overhead**: Role initialization per device
5. **Variable Context Switching**: Ansible variable scope changes per iteration

## 🔍 Detailed Timeline Analysis

From log timestamps:
```
Device 1:  1767473515 → 1767473523  (8 seconds)
Device 2:  1767473523 → 1767473528  (5 seconds)
Device 3:  1767473528 → 1767473534  (6 seconds)
...
Device 17: 1767473600 → 1767473605  (5 seconds)
```

**Per-Device Breakdown:**
- Netbox device fetch: ~200ms
- Python processing: ~300ms
- Zabbix migration role: **~4-5 seconds** ⚠️
- Result collection: ~100ms

## ⚡ Optimization Strategies

### Strategy 1: Move Logic Outside Loop (Recommended)

**Before (Current):**
```yaml
- name: Process devices
  include_role:
    name: zabbix_migration
  loop: "{{ netbox_devices }}"
  # Entire role runs 17 times
```

**After (Optimized):**
```yaml
# Load mappings ONCE
- name: Load all mappings
  include_tasks: roles/zabbix_migration/tasks/load_mappings.yml
  run_once: true

# Process devices in batch
- name: Process all devices
  include_tasks: roles/zabbix_migration/tasks/process_single_device.yml
  loop: "{{ netbox_devices }}"
  # Only core logic runs per device
```

**Expected Improvement:** 3-4 seconds per device → **0.5-1 second per device**

### Strategy 2: Parallel Processing with async

```yaml
- name: Process devices in parallel
  include_role:
    name: zabbix_migration
  loop: "{{ netbox_devices }}"
  async: 300
  poll: 0
  register: async_results

- name: Wait for all processes
  async_status:
    jid: "{{ item.ansible_job_id }}"
  loop: "{{ async_results.results }}"
  register: async_poll_results
  until: async_poll_results.finished
  retries: 60
```

**Expected Improvement:** 17 devices × 5s = 85s → **~10-15 seconds total** (parallel)

### Strategy 3: Python Batch Processing

Move entire device processing to Python:
```python
# Process all devices in one Python script
for device in devices:
    process_device(device)
    # No Ansible overhead per iteration
```

**Expected Improvement:** **~5-10 seconds total** for all 17 devices

## 📈 Comparison Table

| Approach | Time for 17 Devices | Complexity | Recommendation |
|----------|---------------------|------------|----------------|
| Current (Role per device) | 90s | Low | ❌ Not recommended |
| Strategy 1 (Optimized tasks) | 10-20s | Medium | ✅ **Best balance** |
| Strategy 2 (Parallel async) | 10-15s | High | ⚠️ Complex error handling |
| Strategy 3 (Pure Python) | 5-10s | Very High | ⚠️ Loses Ansible benefits |

## 🎯 Recommended Implementation (Strategy 1)

### Step 1: Refactor role structure

```
roles/zabbix_migration/tasks/
├── main.yml (orchestrator)
├── load_mappings.yml (run once)
├── process_single_device.yml (loop this)
└── finalize.yml (run once)
```

### Step 2: Update main playbook

```yaml
- name: Initialize migration
  include_tasks: roles/zabbix_migration/tasks/load_mappings.yml
  run_once: true

- name: Process devices efficiently
  include_tasks: roles/zabbix_migration/tasks/process_single_device.yml
  loop: "{{ netbox_devices }}"
  loop_control:
    loop_var: device_item
    label: "{{ device_item.name }}"

- name: Finalize migration
  include_tasks: roles/zabbix_migration/tasks/finalize.yml
  run_once: true
```

### Step 3: Measure improvement

Add timing:
```yaml
- name: Start timer
  set_fact:
    start_time: "{{ ansible_date_time.epoch }}"

- name: Process devices
  # ... processing ...

- name: Calculate duration
  debug:
    msg: "Processed {{ netbox_devices | length }} devices in {{ ansible_date_time.epoch | int - start_time | int }} seconds"
```

## 🚀 Quick Win: Reduce Task Verbosity

While refactoring, reduce overhead:

```yaml
# Add to ansible.cfg or playbook header
[defaults]
callback_whitelist = profile_tasks
display_skipped_hosts = no  # Don't show skipped tasks

# In playbook
- name: Process devices
  # ... tasks ...
  no_log: true  # For non-critical tasks
  changed_when: false  # Reduce change tracking overhead
```

**Expected Improvement:** 5-10% faster

## 📝 Implementation Priority

1. ✅ **[DONE]** Fix mail collection error
2. 🔄 **[NEXT]** Refactor role structure (Strategy 1)
3. 🔄 **[OPTIONAL]** Add timing/profiling
4. 🔄 **[FUTURE]** Consider parallel processing for 100+ devices

## 🔗 Related Files

- Main playbook: `playbooks/netbox_to_zabbix_migration.yml`
- Device processing: `roles/netbox_to_zabbix/tasks/process_device.yml`
- Zabbix migration role: `roles/zabbix_migration/tasks/main.yml`

---

**Note:** Performance optimization is critical for large-scale migrations (100+ devices).
Current approach would take **~8 minutes for 100 devices**. Optimized approach: **~1-2 minutes**.



