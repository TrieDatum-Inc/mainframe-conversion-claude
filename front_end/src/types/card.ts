export interface CardListItem { card_num: string; card_acct_id: string; card_active_status: string; }
export interface CardListResponse { items: CardListItem[]; page: number; page_size: number; has_next_page: boolean; next_cursor: string | null; prev_cursor: string | null; total_on_page: number; }
export interface CardDetail { card_num: string; card_acct_id: string; card_cvv_cd: string | null; card_embossed_name: string | null; card_active_status: string; expiry_month: number | null; expiry_year: number | null; expiry_day: number | null; updated_at: string; }
export interface CardUpdateRequest { card_embossed_name: string; card_active_status: "Y" | "N"; expiry_month: number; expiry_year: number; updated_at: string; }
export interface CardUpdateResponse { card_num: string; card_acct_id: string; card_embossed_name: string | null; card_active_status: string; expiry_month: number | null; expiry_year: number | null; expiry_day: number | null; updated_at: string; message: string; }
export interface CardListParams { cursor?: string; acct_id?: string; card_num_filter?: string; page_size?: number; page?: number; }
export interface ApiError { detail: string | Array<{ msg: string; loc: string[] }>; }
