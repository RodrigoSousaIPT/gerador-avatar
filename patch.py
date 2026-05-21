import os
for root, _, files in os.walk('Wav2Lip'):
    for file in files:
        if file.endswith('.py'):
            p = os.path.join(root, file)
            with open(p, 'r', encoding='utf-8') as f:
                c = f.read()
            n = c.replace('np.float', 'float').replace('np.int', 'int').replace('np.bool', 'bool')
            if c != n:
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(n)
