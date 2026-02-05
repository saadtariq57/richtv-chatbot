## **Purpose of the Response Validator**

1. Ensure the LLM **only reports numbers or facts that exist in the context** fetched from your data sources (PriceFetcher, FundamentalsFetcher, NewsFetcher).
2. Assign a **confidence score** to the answer.
3. Reject or flag any output that cannot be verified.
4. (Future phase) Attach citations if external sources are used.

---

## **How It Works — Step by Step**

### **Step 1: Receive LLM Output**

- LLM returns a text string based on the context.
- Example:

```
"NVDA stock closed at 875.23 USD today, down 3.8% from yesterday."

```

### **Step 2: Extract Numbers & Entities**

- Use a lightweight parser in Python (regex or NLP) to pull:
    - Ticker symbols (NVDA)
    - Prices (875.23)
    - Percent changes (-3.8%)
    - Dates/timestamps
- Compare these values to your **structured context** built from the fetchers:

```json
{
  "ticker": "NVDA",
  "price": 875.23,
  "change_percent": -3.8,
  "source": "APA internal data",
  "timestamp": "2025-12-21T12:00:00"
}

```

---

### **Step 3: Verify Against Context**

- Check if **all numbers/claims mentioned by LLM exist in the context**.
- If everything matches → pass
- If something is missing or mismatched → flag/reject

Example failure:

```
"NVDA stock closed at 880 USD today"  ← 880 does not match context 875.23
```

- Validator will either:
    - Replace the number with context value
    - Or reject the response entirely

---

### **Step 4: Assign Confidence Score**

- If all data aligns → high confidence (e.g., 0.9–1.0)
- If partially matches → medium confidence (0.5–0.8)
- If LLM hallucinated → low confidence (0–0.5) or reject
- Store this confidence along with the answer in Postgres.

---

### **Step 5: Return Structured JSON**

- Only return **validated answers** to the client:

```json
{
  "answer": "NVDA stock closed at 875.23 USD today, down 3.8% from yesterday.",
  "confidence": 0.95,
  "data_timestamp": "2025-12-21T12:00:00"
}

```

- No citations yet, since it’s internal APA data.

---

## **Key Principles**

1. **Validator is your “truth guard”** — nothing leaves the system unless verified.
2. Works purely from **structured context**, never from LLM hallucinations.
3. Can be extended in the future for **citations, multiple sources, or semantic checks**.
4. Should be lightweight — do not let it slow down response time significantly.

---