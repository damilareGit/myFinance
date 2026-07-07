export type CategoryKind = "income" | "expense" | "transfer";

export interface User {
  id: number;
  email: string;
  display_name: string;
}

export interface Category {
  id: number;
  name: string;
  kind: CategoryKind;
  is_custom: boolean;
}

export interface CategoryRule {
  id: number;
  category_id: number;
  keyword: string;
  is_custom: boolean;
}

export interface Transaction {
  date: string;
  description: string;
  debit: number;
  credit: number;
  balance: number | null;
  account: string;
  currency: string;
  category_id: number;
  category_name: string;
  category_kind: CategoryKind;
  source_page: number | null;
  tx_hash: string;
}

export interface CategoryTotal {
  category_id: number;
  category_name: string;
  category_kind: CategoryKind;
  debit: number;
  credit: number;
}

export interface MonthlySummary {
  month: string;
  income: number;
  spend: number;
  savings_contributed: number;
  min_balance: number | null;
  savings_rate_pct: number;
}

export interface Insight {
  tone: "good" | "warn" | "neutral";
  message: string;
}

export interface ParseWarning {
  page: number | null;
  message: string;
}

export interface StatementAnalysis {
  transactions: Transaction[];
  category_totals: CategoryTotal[];
  monthly_summaries: MonthlySummary[];
  insights: Insight[];
  total_income: number;
  total_spend: number;
  overall_savings_rate_pct: number;
  primary_currency: string;
  warnings: ParseWarning[];
}

export type GoalKind = "savings" | "debt";

export interface Goal {
  id: number;
  name: string;
  kind: GoalKind;
  target_amount: number;
  current_amount: number;
  remaining_amount: number;
  progress_pct: number;
  target_date: string | null;
  currency: string;
  pace_message: string | null;
}
