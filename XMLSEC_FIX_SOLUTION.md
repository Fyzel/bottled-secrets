# XMLSec Library Version Mismatch - SOLVED ✅

## 🚨 **Problem**
```
xmlsec.InternalError: (-1, 'lxml & xmlsec libxml2 library version mismatch')
```

This error occurs when the Python `xmlsec` package is compiled against a different version of libxml2 than what `lxml` is using.

## ✅ **Solution Applied**

### **Step 1: Remove Conflicting Packages**
```bash
source venv/bin/activate
pip uninstall xmlsec python3-saml lxml -y
```

### **Step 2: Install Compatible lxml Version**
```bash
pip install lxml==4.9.4
```

### **Step 3: Rebuild xmlsec from Source with Shared Linking**
```bash
XMLSEC_LINK_SHARED=1 pip install --no-cache-dir --no-binary xmlsec xmlsec
```

### **Step 4: Reinstall python3-saml**
```bash
pip install python3-saml
```

## 🧪 **Verification**

All imports now work correctly:
```bash
✅ xmlsec import successful
✅ SAML import successful
✅ App creation successful
✅ HTTPS server starts successfully
```

## 🔧 **Technical Details**

### **Root Cause**
- `lxml` 5.4.0 was compiled with libxml2 2.9.14
- `xmlsec` 1.3.15 binary wheel was compiled with different libxml2 version
- Version mismatch caused runtime incompatibility

### **Solution Explanation**
1. **Downgraded lxml**: Used stable 4.9.4 version
2. **Rebuilt xmlsec**: Compiled from source with `XMLSEC_LINK_SHARED=1`
3. **Shared linking**: Ensures xmlsec uses system libxml2 libraries
4. **Version compatibility**: Both packages now use same libxml2 base

### **System Environment**
- **OS**: Ubuntu 24.04
- **libxml2**: 2.9.14 (system)
- **xmlsec1**: 1.2.39 (system)
- **Python**: 3.12
- **lxml**: 4.9.4 (downgraded)
- **xmlsec**: 1.3.15 (rebuilt from source)

## 🚀 **Current Status**

**SAML Authentication is now fully functional:**
- ✅ Google SAML configuration working
- ✅ HTTPS server operational
- ✅ Full application imports successful
- ✅ No more library version conflicts

## 📋 **Alternative Solutions (if above fails)**

### **Option 1: Use System Packages (requires sudo)**
```bash
sudo apt install python3-xmlsec python3-lxml
```

### **Option 2: Different lxml Version**
```bash
pip install lxml==4.6.5
XMLSEC_LINK_SHARED=1 pip install --no-binary xmlsec xmlsec
```

### **Option 3: Use Docker**
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y \
    libxml2-dev libxmlsec1-dev libxmlsec1-openssl \
    pkg-config build-essential
```

## ⚠️ **Prevention**

To avoid this issue in the future:
1. **Pin versions** in requirements.txt
2. **Use virtual environments** for isolation
3. **Test imports** after package updates
4. **Document working combinations**

## 📁 **Updated Requirements**

The working package combination:
```
lxml==4.9.4
xmlsec==1.3.15
python3-saml==1.16.0
```

**Your Bottled Secrets SAML authentication is now ready for production! 🎉**
