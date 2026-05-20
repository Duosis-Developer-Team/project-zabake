# Gitea Setup Guide — datalake-collectors

## Two repositories

| Repo | Visibility | GitHub mirror | Purpose |
|------|------------|---------------|---------|
| `datalake-collectors-mappings` | Internal | Yes (from `project-zabake/datalake-collectors/mappings`) | YAML mappings only |
| `datalake-collectors-vault` | **Private** | **No** | Secrets and manual-only sections |

## 1. Create mappings mirror repo

1. Gitea → New Repository → `datalake-collectors-mappings` (internal).
2. Settings → Mirror → GitHub `project-zabake` path or sync `datalake-collectors/mappings` periodically.
3. AWX SCM can use full `project-zabake` instead if preferred (playbook ships with mappings in-tree).

## 2. Create vault repo (Gitea-only)

1. New Repository → `datalake-collectors-vault` (**private**).
2. Copy structure from [datalake-collectors-vault-template](../../datalake-collectors-vault-template/README.md).
3. Restrict collaborators to AWX service account and platform admins.

## 3. Gitea token for AWX

1. User Settings → Applications → Generate Token.
2. Scope: read repository (vault repo).
3. AWX Custom Credential Type → inject `gitea_vault_token` into extra vars.

## 4. SSH to Proxy NiFi

1. Generate SSH key pair for AWX.
2. Add public key to `nifi` user on each proxy (`proxy_assignment.yml`).
3. AWX Machine Credential → username `nifi`, private key.

## 5. HMDL job triggering Gitea mirror (optional)

Schedule an AWX job or webhook that runs `git pull` on the mappings mirror before collector sync if mappings are maintained only on GitHub.
