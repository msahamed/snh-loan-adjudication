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
  {
    id: "credit-reject",
    short: "Credit decline",
    title: "Credit threshold failure",
    description: "The reported credit score is below the active minimum.",
    accent: "red",
    application: {
      age: 36, credit_score: 645, annual_income_usd: 74000, debt_to_income_ratio_percent: 28,
      employment_status: "employed_full_time", current_employment_duration_months: 28,
      residency_status: "US_Citizen", has_bankruptcy_recent: false,
      requested_amount_usd: 10000, has_verifiable_bank_account: true,
    },
    model: { decision: "REJECT", failed_rule_ids: ["RULE-CREDIT-001"], explanation: "The reported credit score is below the required minimum." },
    messages: [
      ["assistant", "How much would you like to borrow?"], ["user", "$10,000 for a used car."],
      ["assistant", "What are your age, annual income, credit score, and DTI?"], ["user", "I’m 36, earn $74,000, my score is 645, and DTI is 28%."],
      ["assistant", "Please confirm employment, residency, bankruptcy history, and an active bank account."], ["user", "Full-time for 28 months, U.S. citizen, no recent bankruptcy, and my bank account is active."],
    ],
  },
  {
    id: "boundary-approve",
    short: "Boundary accept",
    title: "Exact policy boundaries",
    description: "Every value sits exactly on an allowed policy boundary.",
    accent: "green",
    application: {
      age: 18, credit_score: 670, annual_income_usd: 30000, debt_to_income_ratio_percent: 40,
      employment_status: "employed_part_time", current_employment_duration_months: 6,
      residency_status: "Permanent_Resident", has_bankruptcy_recent: false,
      requested_amount_usd: 15000, has_verifiable_bank_account: true,
    },
    model: { decision: "APPROVE", failed_rule_ids: [], explanation: "The application meets the current requirements." },
    messages: [
      ["assistant", "How much are you requesting?"], ["user", "$15,000."],
      ["assistant", "Please share your age, income, credit score, and DTI."], ["user", "I’m 18, earn $30,000, have a 670 score, and my DTI is 40%."],
      ["assistant", "What is your employment and residency status?"], ["user", "Part-time for six months and I’m a permanent resident. No recent bankruptcy, and I have an active bank account."],
    ],
  },
  {
    id: "dti-reject",
    short: "DTI decline",
    title: "High debt-to-income",
    description: "Income and credit pass, but the reported DTI exceeds policy.",
    accent: "red",
    application: {
      age: 44, credit_score: 720, annual_income_usd: 90000, debt_to_income_ratio_percent: 47,
      employment_status: "self_employed", current_employment_duration_months: 60,
      residency_status: "US_Citizen", has_bankruptcy_recent: false,
      requested_amount_usd: 25000, has_verifiable_bank_account: true,
    },
    model: { decision: "REJECT", failed_rule_ids: ["RULE-DTI-001"], explanation: "The reported debt-to-income ratio exceeds the allowed maximum." },
    messages: [
      ["assistant", "How much would you like to borrow?"], ["user", "$25,000 for my business."],
      ["assistant", "Please share your age, income, credit score, and DTI."], ["user", "I’m 44, earn about $90,000, credit is 720, and DTI is 47%."],
      ["assistant", "How long have you been self-employed, and can you confirm the remaining checks?"], ["user", "Five years. U.S. citizen, no recent bankruptcy, and yes, I have a verified account."],
    ],
  },
  {
    id: "amount-review",
    short: "Amount review",
    title: "Loan amount escalation",
    description: "The amount requested exceeds half of reported annual income.",
    accent: "amber",
    application: {
      age: 31, credit_score: 690, annual_income_usd: 60000, debt_to_income_ratio_percent: 30,
      employment_status: "employed_full_time", current_employment_duration_months: 20,
      residency_status: "Permanent_Resident", has_bankruptcy_recent: false,
      requested_amount_usd: 32000, has_verifiable_bank_account: true,
    },
    model: { decision: "APPROVE", failed_rule_ids: [], explanation: "The application meets the current requirements." },
    messages: [
      ["assistant", "How much would you like to borrow?"], ["user", "$32,000 to consolidate several balances."],
      ["assistant", "What are your age, income, credit score, and DTI?"], ["user", "31, $60,000 a year, 690 credit, and 30% DTI."],
      ["assistant", "Please confirm employment, residency, bankruptcy history, and bank account."], ["user", "Full-time for 20 months, permanent resident, no recent bankruptcy, and an active bank account."],
    ],
  },
  {
    id: "bankruptcy-reject",
    short: "Bankruptcy decline",
    title: "Recent bankruptcy",
    description: "A recent bankruptcy triggers an automatic policy decline.",
    accent: "red",
    application: {
      age: 48, credit_score: 755, annual_income_usd: 110000, debt_to_income_ratio_percent: 18,
      employment_status: "employed_full_time", current_employment_duration_months: 70,
      residency_status: "US_Citizen", has_bankruptcy_recent: true,
      requested_amount_usd: 25000, has_verifiable_bank_account: true,
    },
    model: { decision: "REJECT", failed_rule_ids: ["RULE-BANKRUPTCY-001"], explanation: "A recent bankruptcy does not meet the current requirement." },
    messages: [
      ["assistant", "How much are you applying for?"], ["user", "$25,000."],
      ["assistant", "Please share your age, income, credit score, and DTI."], ["user", "I’m 48, earn $110,000, my score is 755, and DTI is 18%."],
      ["assistant", "Any recent bankruptcy? I also need employment, residency, and bank-account details."], ["user", "I filed recently. I’ve worked full-time for 70 months, I’m a U.S. citizen, and my bank account is verified."],
    ],
  },
  {
    id: "bank-account-reject",
    short: "Account decline",
    title: "Bank account not verified",
    description: "The applicant cannot confirm an active, verifiable bank account.",
    accent: "red",
    application: {
      age: 39, credit_score: 702, annual_income_usd: 72000, debt_to_income_ratio_percent: 33,
      employment_status: "self_employed", current_employment_duration_months: 18,
      residency_status: "Permanent_Resident", has_bankruptcy_recent: false,
      requested_amount_usd: 18000, has_verifiable_bank_account: false,
    },
    model: { decision: "REJECT", failed_rule_ids: ["RULE-BANKACCTS-001"], explanation: "An active, verifiable bank account was not confirmed." },
    messages: [
      ["assistant", "How much would you like to borrow?"], ["user", "$18,000."],
      ["assistant", "Please share your age, income, credit score, and DTI."], ["user", "I’m 39, earn $72,000, have a 702 score, and my DTI is 33%."],
      ["assistant", "Please confirm employment, residency, bankruptcy history, and a verifiable bank account."], ["user", "Self-employed for 18 months, permanent resident, no recent bankruptcy. I can’t verify my bank account right now."],
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
