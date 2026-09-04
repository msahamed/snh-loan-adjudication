export const rules = [
  { id: "RULE-AGE-001", field: "age", label: "Age", operator: ">=", expected: 18, action: "REJECT" },
  { id: "RULE-CREDIT-001", field: "credit_score", label: "Credit score", operator: ">=", expected: 670, action: "REJECT" },
  { id: "RULE-INCOME-001", field: "annual_income_usd", label: "Annual income", operator: ">=", expected: 30000, action: "REJECT" },
  { id: "RULE-DTI-001", field: "debt_to_income_ratio_percent", label: "Debt-to-income", operator: "<=", expected: 40, action: "REJECT" },
  { id: "RULE-EMPLOY-001", field: "employment_status", label: "Employment", operator: "in", expected: ["employed_full_time", "employed_part_time", "self_employed", "retired"], action: "REJECT" },
  { id: "RULE-EMPLOY-002", field: "current_employment_duration_months", label: "Employment duration", operator: ">=", expected: 6, action: "FLAG_REVIEW" },
  { id: "RULE-RESIDENCY-001", field: "residency_status", label: "Residency", operator: "in", expected: ["US_Citizen", "Permanent_Resident"], action: "REJECT" },
  { id: "RULE-BANKRUPTCY-001", field: "has_bankruptcy_recent", label: "Recent bankruptcy", operator: "is", expected: false, action: "REJECT" },
  { id: "RULE-LOANAMT-001", field: "requested_amount_usd", label: "Loan-to-income", operator: "income ×", expected: 0.5, action: "FLAG_REVIEW" },
  { id: "RULE-BANKACCTS-001", field: "has_verifiable_bank_account", label: "Bank account", operator: "is", expected: true, action: "REJECT" },
];

export const examples = [
  {
    id: "approve",
    short: "Accept",
    title: "Clean approval",
    description: "All reported values satisfy the active policy.",
    accent: "green",
    application: {
      age: 34,
      credit_score: 742,
      annual_income_usd: 84000,
      debt_to_income_ratio_percent: 24,
      employment_status: "employed_full_time",
      current_employment_duration_months: 36,
      residency_status: "US_Citizen",
      has_bankruptcy_recent: false,
      requested_amount_usd: 20000,
      has_verifiable_bank_account: true,
    },
    model: { decision: "APPROVE", failed_rule_ids: [], explanation: "The application meets the current requirements." },
    messages: [
      ["assistant", "Hi, I can help with your personal-loan application. How much would you like to borrow?"],
      ["user", "I need $20,000 for home repairs."],
      ["assistant", "Thanks. Please tell me your age, annual income, and current credit score."],
      ["user", "I’m 34, earn $84,000 a year, and my score is 742."],
      ["assistant", "What is your debt-to-income ratio and current employment situation?"],
      ["user", "My DTI is 24%. I’ve worked full-time in this role for three years."],
      ["assistant", "Last check: residency, recent bankruptcy, and an active bank account?"],
      ["user", "U.S. citizen, no bankruptcy in seven years, and yes, my account is active."],
    ],
  },
  {
    id: "reject",
    short: "Corrected reject",
    title: "Model error caught",
    description: "The model approves, but verified income is below policy.",
    accent: "red",
    application: {
      age: 68,
      credit_score: 712,
      annual_income_usd: 29500,
      debt_to_income_ratio_percent: 19,
      employment_status: "retired",
      current_employment_duration_months: 46,
      residency_status: "US_Citizen",
      has_bankruptcy_recent: false,
      requested_amount_usd: 14000,
      has_verifiable_bank_account: true,
    },
    model: { decision: "APPROVE", failed_rule_ids: [], explanation: "The application meets the current requirements." },
    messages: [
      ["assistant", "How much would you like to borrow?"],
      ["user", "$14,000."],
      ["assistant", "Please share your age, annual income, and credit score."],
      ["user", "I’m 68, retired, make $29,500 a year, and my score is 712."],
      ["assistant", "How long have you had this income, and what is your DTI?"],
      ["user", "Forty-six months. My DTI is 19%."],
      ["assistant", "Do you meet the residency, bankruptcy, and bank-account requirements?"],
      ["user", "I’m a U.S. citizen, no recent bankruptcy, and I have an active bank account."],
    ],
  },
  {
    id: "review",
    short: "Escalate",
    title: "Human review",
    description: "Two review rules fail; no automatic rejection applies.",
    accent: "amber",
    application: {
      age: 29,
      credit_score: 710,
      annual_income_usd: 68000,
      debt_to_income_ratio_percent: 31,
      employment_status: "employed_full_time",
      current_employment_duration_months: 3,
      residency_status: "Permanent_Resident",
      has_bankruptcy_recent: false,
      requested_amount_usd: 50000,
      has_verifiable_bank_account: true,
    },
    model: { decision: "REVIEW", failed_rule_ids: ["RULE-EMPLOY-002"], explanation: "The current employment period is below the required minimum." },
    messages: [
      ["assistant", "How much would you like to borrow?"],
      ["user", "$50,000 to consolidate debt."],
      ["assistant", "Please share your age, income, credit score, and DTI."],
      ["user", "I’m 29, earn $68,000, my score is 710, and DTI is 31%."],
      ["assistant", "Tell me about your employment and residency."],
      ["user", "Full-time for three months. I’m a permanent resident."],
      ["assistant", "Any recent bankruptcy, and do you have an active bank account?"],
      ["user", "No recent bankruptcy. Yes, I have an active account."],
    ],
  },
  {
    id: "collect",
    short: "Need information",
    title: "Incomplete application",
    description: "Age is unresolved, so no lending decision is made.",
    accent: "blue",
    application: {
      age: null,
      credit_score: 695,
      annual_income_usd: 62000,
      debt_to_income_ratio_percent: 29,
      employment_status: "employed_full_time",
      current_employment_duration_months: 12,
      residency_status: "US_Citizen",
      has_bankruptcy_recent: false,
      requested_amount_usd: 20000,
      has_verifiable_bank_account: true,
    },
    model: { decision: "COLLECTING_INFORMATION", failed_rule_ids: [], explanation: "More information is needed for: age." },
    messages: [
      ["assistant", "How much would you like to borrow?"],
      ["user", "$20,000."],
      ["assistant", "Please share your age, annual income, and credit score."],
      ["user", "I’d rather not say my age yet. I earn $62,000 and my score is 695."],
      ["assistant", "I can continue collecting information, but I cannot assess eligibility without your age."],
    ],
  },
];

export const decisionMeta = {
  APPROVE: { label: "Accept", route: "Straight-through approval", tone: "green", customer: "Your application meets the current requirements." },
  REJECT: { label: "Reject", route: "Decline with verified reason", tone: "red", customer: "We’re unable to approve this application based on the current requirements." },
  REVIEW: { label: "Escalate", route: "Human credit review", tone: "amber", customer: "Your application needs a specialist review before we can make a final decision." },
  COLLECTING_INFORMATION: { label: "Continue", route: "Return to chatbot", tone: "blue", customer: "I need a little more information before assessing your application." },
};

export const projectLinks = {
  github: "https://github.com/msahamed/snh-loan-adjudication",
  model: "https://huggingface.co/sabber/snh-qwen3-1.7b-loan-adjudication-lora",
  dataset: "https://huggingface.co/datasets/sabber/snh-loan-adjudication-synthetic",
};

export function getExample(caseId) {
  return examples.find((item) => item.id === caseId);
}

function passesRule(rule, application) {
  const actual = application[rule.field];
  if (actual === null || actual === undefined) return null;
  if (rule.operator === ">=") return actual >= rule.expected;
  if (rule.operator === "<=") return actual <= rule.expected;
  if (rule.operator === "in") return rule.expected.includes(actual);
  if (rule.operator === "is") return actual === rule.expected;
  if (rule.operator === "income ×") return actual <= application.annual_income_usd * rule.expected;
  return false;
}

export function humanize(value) {
  if (value === null || value === undefined) return "Not provided";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function observedValue(rule, application) {
  const value = application[rule.field];
  if (value === null || value === undefined) return "Missing";
  if (["annual_income_usd", "requested_amount_usd"].includes(rule.field)) return `$${value.toLocaleString()}`;
  if (rule.field === "debt_to_income_ratio_percent") return `${value}%`;
  if (rule.field === "current_employment_duration_months") return `${value} months`;
  return humanize(value);
}

export function ruleRequirement(rule, application) {
  if (rule.operator === "income ×") return `≤ $${(application.annual_income_usd * rule.expected).toLocaleString()}`;
  if (Array.isArray(rule.expected)) return rule.expected.map(humanize).join(" or ");
  if (typeof rule.expected === "boolean") return rule.expected ? "Yes" : "No";
  if (rule.field === "annual_income_usd") return `≥ $${rule.expected.toLocaleString()}`;
  if (rule.field === "debt_to_income_ratio_percent") return `≤ ${rule.expected}%`;
  return `${rule.operator} ${rule.expected}`;
}

function explanationFor(rule, application) {
  const actual = application[rule.field];
  const explanations = {
    "RULE-AGE-001": `The applicant is ${actual}. The minimum age is 18.`,
    "RULE-CREDIT-001": `The reported credit score is ${actual}. The minimum is 670.`,
    "RULE-INCOME-001": `The reported annual income is $${actual.toLocaleString()}. The minimum is $30,000.`,
    "RULE-DTI-001": `The reported debt-to-income ratio is ${actual}%. The maximum is 40%.`,
    "RULE-EMPLOY-001": "The reported employment status does not meet the current requirement.",
    "RULE-EMPLOY-002": `The reported employment duration is ${actual} months. At least 6 months is required.`,
    "RULE-RESIDENCY-001": "The reported residency status does not meet the current requirement.",
    "RULE-BANKRUPTCY-001": "A bankruptcy was reported within the configured lookback period.",
    "RULE-LOANAMT-001": `The requested amount is $${actual.toLocaleString()}. The maximum for the reported income is $${(application.annual_income_usd * 0.5).toLocaleString()}.`,
    "RULE-BANKACCTS-001": "An active, verifiable bank account was not confirmed.",
  };
  return explanations[rule.id];
}

export function adjudicate(application) {
  const checks = rules.map((rule) => ({ ...rule, passed: passesRule(rule, application) }));
  const missing = checks.filter((check) => check.passed === null);
  if (missing.length) {
    return {
      decision: "COLLECTING_INFORMATION",
      failed_rule_ids: [],
      explanation: `More information is needed for: ${missing.map((item) => item.label.toLowerCase()).join(", ")}.`,
      checks,
    };
  }
  const failed = checks.filter((check) => check.passed === false);
  const decision = failed.some((item) => item.action === "REJECT")
    ? "REJECT"
    : failed.some((item) => item.action === "FLAG_REVIEW") ? "REVIEW" : "APPROVE";
  return {
    decision,
    failed_rule_ids: failed.map((item) => item.id),
    explanation: failed.length
      ? failed.map((item) => explanationFor(item, application)).join(" ")
      : "Based on the information provided, the application meets the current requirements.",
    checks,
  };
}
