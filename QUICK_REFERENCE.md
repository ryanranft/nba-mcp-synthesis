# 🚀 Quick Reference - Three-Way Ollama Deployment

## ⚡ Quick Commands

```bash
# Check status of all deployments
./check_all_ollama.sh

# Switch web interface to local
./switch_to_local.sh

# Switch web interface to AWS
./switch_to_aws.sh

# Start web chat
./start_ollama_chat.sh

# AWS instance control
aws ec2 stop-instances --instance-ids i-06ec10b8f8fbe0ee4    # Stop (save $)
aws ec2 start-instances --instance-ids i-06ec10b8f8fbe0ee4   # Start
```

---

## 📍 Three Deployments

| Location | URL | Models | Cost |
|----------|-----|--------|------|
| 🏠 Local | localhost:11434 | Qwen 32B, GPT-OSS 20B | FREE |
| ☁️ AWS | 34.226.246.126:11434 | Qwen 32B | $0.33/hr |
| ⚙️ Cursor | (all above) | All 3 models | - |

---

## 🎯 Which to Use?

- **Quick query** → 🏠 Local GPT-OSS 20B (fastest)
- **Normal work** → 🏠 Local Qwen 32B (free, private)
- **Long analysis** → ☁️ AWS Qwen 32B (reliable, powerful)

---

## 🔧 In Cursor

1. **Reload window:** `Cmd+Shift+P` → "Reload Window"
2. **Click model selector** (bottom right)
3. **Choose:**
   - 🏠 Local Ollama Qwen2.5-Coder 32B
   - ☁️ AWS Ollama Qwen2.5-Coder 32B
   - 🏠 Local Ollama GPT-OSS 20B

---

## 💰 Daily Cost Estimate

**If you leave AWS running 24/7:** $7.92/day

**Smart usage (8 hours/day):** $2.64/day

**Use local + stop AWS when done:** $0/day! 🎉

---

## 🧪 Test Commands

```bash
# Test local
curl http://localhost:11434/api/tags

# Test AWS
curl http://34.226.246.126:11434/api/tags

# Quick chat test
curl http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5-coder:32b","prompt":"Hi","stream":false}'
```

---

## 📚 Full Documentation

- `THREE_WAY_DEPLOYMENT_COMPLETE.md` - Complete guide
- `DEPLOYMENT_SUCCESS.md` - AWS details
- `OLLAMA_MCP_SETUP_GUIDE.md` - Local setup
- `AWS_OLLAMA_GUIDE.md` - Cloud setup

---

## 🆘 Troubleshooting

**Issue:** Cursor doesn't show model options
**Fix:** Reload window (`Cmd+Shift+P` → "Reload Window")

**Issue:** AWS not responding
**Fix:** Start instance: `aws ec2 start-instances --instance-ids i-06ec10b8f8fbe0ee4`

**Issue:** Local Ollama not running
**Fix:** Click Ollama icon in menu bar → check it's running

---

## 🎉 You're All Set!

**3 locations ✅**
**3 models ✅**
**100+ NBA tools ✅**
**Full control ✅**

**Happy coding! 🏀🤖**


