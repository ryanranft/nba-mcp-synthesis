# 🎉 Dual Deployment Plan - In Progress!

## ✅ Part 1: CPU Instance (DEPLOYED!)

**Instance ID:** i-08b57eaa405701fcb
**Public IP:** 34.226.246.126
**Type:** t3.2xlarge (8 vCPU, 32GB RAM)
**Cost:** $0.33/hour (~$40/month at 4 hrs/day)
**Status:** Installing Ollama now (10-15 minutes)

### What's Happening Now:
- ✅ Instance is running
- ⏳ Installing Ollama
- ⏳ Downloading Qwen2.5-Coder 32B model (40GB)
- ⏳ Configuring system

**Ready in:** 10-15 minutes

---

## ⏳ Part 2: GPU Limit Request (YOUR ACTION NEEDED!)

### Quick Steps (2 minutes):

The AWS console is already open in your browser!

1. **Click "Request quota increase"**

2. **Fill in the form:**
   - Service quota name: "Running On-Demand G and VT instances"
   - Desired quota value: **32**
   - Use case description: **"Running Ollama AI models (72B parameters) for NBA data analytics and model context protocol (MCP) tool integration"**

3. **Submit**

4. **Wait for approval email** (usually 24-48 hours)

### Direct Link (if browser closed):
```
https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-DB2E81BA
```

---

## 🎯 Your Timeline

### TODAY (Next 15 minutes)
```
⏰ Now + 10 min:  CPU instance ready
⏰ Now + 12 min:  Run configuration
⏰ Now + 15 min:  Start chatting with AWS Ollama!
```

**Commands:**
```bash
# In 10-15 minutes, run:
cd /Users/ryanranft/nba-mcp-synthesis
./configure_ollama_aws.sh
./start_ollama_chat.sh
```

### IN 24-48 HOURS (After GPU Approval)
```
📧 Get approval email
🚀 Deploy GPU version (10 seconds)
⚡ Switch to 72B model
🎉 Even faster responses!
```

**Commands:**
```bash
# After GPU approval:
./deploy_ollama_aws.sh  # GPU version with 72B!
./configure_ollama_aws.sh  # Point to new instance
aws ec2 stop-instances --instance-ids i-08b57eaa405701fcb  # Stop CPU to save money
```

---

## 📊 Performance Comparison

| Setup | Speed | Cost/Hour | Model | Available |
|-------|-------|-----------|-------|-----------|
| **Local Mac** | 8 sec | $0 | 32B | Now |
| **CPU (Current)** | 4-6 sec | $0.33 | 32B | **Now** ✅ |
| **GPU (Soon)** | 1-2 sec | $1.00 | 72B | 24-48 hrs |

---

## 💰 Cost Breakdown

### Current Setup (CPU)
- **Per hour:** $0.33
- **4 hours/day:** $40/month
- **8 hours/day:** $79/month

### After GPU Upgrade
- **Per hour:** $1.00
- **4 hours/day:** $120/month
- **8 hours/day:** $240/month

**Note:** GPU is more expensive per hour, but MUCH better value (3x faster, 2.25x larger model, better quality)

---

## 🧪 Testing Your CPU Instance

### In 10-15 minutes, test connection:

```bash
# Test API
curl http://34.226.246.126:11434/api/tags

# Should return model info (once setup complete)
```

### Then configure and chat:

```bash
cd /Users/ryanranft/nba-mcp-synthesis
./configure_ollama_aws.sh
./start_ollama_chat.sh
```

---

## 🔄 Switching to GPU Later

Once GPU is approved:

### Step 1: Deploy GPU Instance
```bash
./deploy_ollama_aws.sh
```

### Step 2: Reconfigure
```bash
./configure_ollama_aws.sh  # Automatically updates to new IP
```

### Step 3: Stop CPU Instance (Save Money)
```bash
aws ec2 stop-instances --instance-ids i-08b57eaa405701fcb
```

**Keep CPU instance for backup!** You can start it anytime if GPU has issues.

---

## 📋 Checklist

### Now (YOUR ACTION):
- [ ] Submit GPU limit increase request in browser
- [ ] Wait 10-15 minutes for CPU setup

### In 10-15 Minutes:
- [ ] Test connection: `curl http://34.226.246.126:11434/api/tags`
- [ ] Run: `./configure_ollama_aws.sh`
- [ ] Run: `./start_ollama_chat.sh`
- [ ] Start using AWS Ollama!

### In 24-48 Hours:
- [ ] Check email for GPU approval
- [ ] Run: `./deploy_ollama_aws.sh`
- [ ] Run: `./configure_ollama_aws.sh`
- [ ] Stop CPU instance
- [ ] Enjoy 72B model!

---

## 🎯 Current Status

```
✅ CPU Instance:  DEPLOYED (Ready in 10-15 min)
⏳ GPU Request:   NEEDS YOUR ACTION (2 minutes)
⏳ GPU Approval:  24-48 hours
```

---

## 💡 Pro Tips

1. **Use CPU while waiting** - Get familiar with AWS setup
2. **Keep both instances** - CPU as backup, GPU for main work
3. **Stop when not using** - Both instances can be stopped to save money
4. **Set billing alerts** - AWS console → Billing → Alerts

---

## 📞 Quick Reference

### CPU Instance
- **IP:** 34.226.246.126
- **Instance ID:** i-08b57eaa405701fcb
- **SSH:** `ssh -i ollama-mcp-key.pem ubuntu@34.226.246.126`
- **API:** http://34.226.246.126:11434
- **Stop:** `aws ec2 stop-instances --instance-ids i-08b57eaa405701fcb`
- **Start:** `aws ec2 start-instances --instance-ids i-08b57eaa405701fcb`

### GPU Request Status
- **Check status:** https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-DB2E81BA
- **View requests:** AWS Console → Service Quotas → Requests

---

## ✨ What You Can Do Today

Once CPU is ready (10-15 min):

1. **Chat with 32B model** - Same as local but faster
2. **Test all 90 MCP tools** - Full NBA analytics
3. **Learn AWS workflow** - Ready for GPU upgrade
4. **Save time vs local** - 2x faster responses

Then upgrade to 72B GPU model in 1-2 days! 🚀

---

**Next Action:** Submit GPU request in browser (2 minutes), then wait 10 minutes and configure!


