# CSD stored with a two-secret envelope (master key + issuer passphrase)

The issuer's e.firma CSD (`.cer` + `.key`) is persisted encrypted at rest with AES-256-GCM under a key `K = SHA-256( master_key ‖ PBKDF2(passphrase, salt, ~200k iters) )`, where `master_key` lives in the app's secret store and the issuer's e.firma passphrase is supplied by the user only to open an in-memory stamping session (never persisted). Decryption therefore requires *both* secrets: a leaked database or the app itself cannot decrypt the CSD without the user's passphrase.

Status: accepted
