# Xenors Code Lab build integration

Extract this ZIP inside your existing `/home/` directory.

Folders:
- `/home/code-lab/`
- `/home/images/code-lab/`

Canonical root: `https://xenors.in/home/code-lab/`

The pages include a section-specific header/footer marked with `data-code-lab-build`. When you send the current build.py, route `/home/code-lab/` separately so the normal Xenors header/footer/read-also is not injected there.

Suggested routing:
```python
if path.startswith("/home/code-lab/"):
    use_code_lab_shell()
else:
    use_main_xenors_shell()
```
