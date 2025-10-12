# ✅ GPU Approval Request Checklist

## 🎯 Are You On The Right Page?

### You Should See:
```
Service: Amazon Elastic Compute Cloud (Amazon EC2)
Quota name: Running On-Demand G and VT instances
Quota code: L-DB2E81BA
Applied quota value: 0
AWS default quota value: 0
```

**✅ If you see this, you're in the right place!**

---

## 📝 Step-by-Step Instructions

### Step 1: Find the Button
Look for an **orange/yellow button** on the right side that says:
- **"Request quota increase"** or
- **"Request increase at account-level"**

**Location:** Top-right area of the page

### Step 2: Click the Button
- A form will appear (either popup or new page)

### Step 3: Fill Out the Form

**Field 1: "Change quota value"**
```
Enter: 32
```

**Field 2: "Use case description" (optional but helps approval)**
```
Running Ollama 72B AI models on g5.xlarge instances for NBA data
analytics, model context protocol (MCP) integration, and basketball
statistics analysis. Educational and development purposes.
```

**Field 3: Contact method**
```
Select: Email (default is fine)
```

### Step 4: Submit
- Click **"Request"** button at bottom
- You should see: "Request submitted successfully"

---

## ✅ Verification Checklist

After submitting, you should:

- [ ] See green success message
- [ ] Get confirmation email (check inbox)
- [ ] See request in "Quota request history" tab
- [ ] Status shows "Pending" or "Case opened"

---

## 📧 What Happens Next

### Immediate:
- ✅ Confirmation email sent
- ✅ Request appears in your Service Quotas dashboard
- ✅ Support ticket created

### Within 24-48 Hours:
- 📧 Approval email (or request for more info)
- ✅ Quota increased to 32
- 🚀 You can deploy GPU version!

### Sometimes:
- ⚡ **Instant approval** (lucky!)
- 📧 Request for more details (just reply to email)

---

## 🚨 Common Issues

### Issue 1: "Request quota increase" button is grayed out
**Solution:** You might not have permissions. Try:
1. Check you're logged in as root/admin user
2. Add IAM permission: `servicequotas:RequestServiceQuotaIncrease`

### Issue 2: Can't find the button
**Solution:**
1. Refresh the page
2. Make sure you're in **us-east-1** region (top-right dropdown)
3. Check the URL matches: `...quotas/L-DB2E81BA`

### Issue 3: Form doesn't submit
**Solution:**
1. Make sure "Desired quota value" is filled: **32**
2. Try a different browser (Chrome, Firefox)
3. Disable browser extensions temporarily

---

## 🔍 How to Check Request Status

### Method 1: Service Quotas Dashboard
1. Go to: https://console.aws.amazon.com/servicequotas
2. Click "Requests" in left sidebar
3. Look for "Running On-Demand G and VT instances"
4. Status should show "Pending" or "Case opened"

### Method 2: Support Center
1. Go to: https://console.aws.amazon.com/support
2. Click "Your support cases"
3. Look for case about "Service Quotas"

---

## 📸 What You Should See (Text Description)

### Before Submitting:
```
┌─────────────────────────────────────────────┐
│ Running On-Demand G and VT instances       │
├─────────────────────────────────────────────┤
│ Quota code: L-DB2E81BA                      │
│ Applied quota value: 0                      │
│ AWS default quota value: 0                  │
│                                             │
│ [Request quota increase] ← Click this!     │
└─────────────────────────────────────────────┘
```

### After Clicking Button:
```
┌─────────────────────────────────────────────┐
│ Request quota increase                      │
├─────────────────────────────────────────────┤
│ Change quota value                          │
│ ┌─────────────────────────────────────────┐ │
│ │ 32                    ← Enter this      │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Use case description (optional)             │
│ ┌─────────────────────────────────────────┐ │
│ │ Running Ollama 72B...                   │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│              [Cancel]  [Request]            │
│                           ↑                 │
│                      Click this!            │
└─────────────────────────────────────────────┘
```

### After Submitting:
```
✅ Request submitted successfully

Your request has been submitted to AWS Support.
You will receive an email confirmation shortly.
```

---

## 💬 Tell Me What You See

**I can't see your browser, but you can tell me:**

1. **What's the page title?**
2. **Do you see "Applied quota value: 0"?**
3. **Do you see a "Request quota increase" button?**
4. **What color is the button?**
5. **Have you clicked it yet?**
6. **If you clicked it, what do you see now?**

---

## 🆘 Need Help?

**Copy and paste what you see** on your screen, and I'll tell you:
- ✅ If you're in the right place
- ✅ What to do next
- ✅ If something looks wrong

---

## ⚡ Quick Test

**To verify you submitted correctly:**

Run this command in your terminal:
```bash
aws service-quotas list-requested-service-quota-change-history \
  --service-code ec2 \
  --region us-east-1 \
  --query 'RequestedQuotas[?QuotaCode==`L-DB2E81BA`]' \
  --output table
```

**If you see a result, your request was submitted!** ✅

---

**Tell me what you see on your screen and I'll help you verify it's correct!** 🔍


