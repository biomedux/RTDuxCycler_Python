from comtypes import client

# Somthing wrong with comtypes 1.1.10
# comtypes==1.1.11 required
print(f"--dshow init")
_modules = list(map(client.GetModule, ["./lib/DirectShow.tlb", "./lib/DexterLib.tlb"]))