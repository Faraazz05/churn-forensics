import os, py_compile
def check():
    bad = []
    for root, dirs, files in os.walk('c:\\Users\\Faraz\\Documents\\customer_health_forensics\\src'):
        for f in files:
            if f.endswith('.py'):
                try:
                    py_compile.compile(os.path.join(root, f), doraise=True)
                except Exception as e:
                    bad.append((f, str(e)))
    print("Compilation check done. Errors:")
    for b in bad:
        print(b)
check()
