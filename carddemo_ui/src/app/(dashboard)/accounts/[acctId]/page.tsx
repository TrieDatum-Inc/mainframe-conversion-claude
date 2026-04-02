'use client';

// ============================================================
// Account Detail / Edit Page
// Mirrors COACTVWC (view) + COACTUPC (update) programs.
// Backend returns nested { account, customer } structure.
// ============================================================

import { use, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Edit2, X, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { accountsApi, getErrorMessage } from '@/lib/api';
import type { AccountWithCustomer } from '@/lib/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { Badge, statusBadge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

function formatCurrency(val: number | undefined | null): string {
  if (val == null) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="border-b border-slate-100 bg-slate-50 px-5 py-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function ReadonlyField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-slate-500">{label}</span>
      <span className="text-sm text-slate-900 break-words">{value ?? '—'}</span>
    </div>
  );
}

function EditForm({ data, onCancel, onSaved }: { data: AccountWithCustomer; onCancel: () => void; onSaved: () => void }) {
  const queryClient = useQueryClient();
  const acct = data.account;
  const cust = data.customer;

  const [form, setForm] = useState({
    active_status: acct.active_status,
    credit_limit: acct.credit_limit,
    cash_credit_limit: acct.cash_credit_limit,
    open_date: acct.open_date ?? '',
    expiration_date: acct.expiration_date ?? '',
    reissue_date: acct.reissue_date ?? '',
    group_id: acct.group_id ?? '',
    first_name: cust.first_name,
    middle_name: cust.middle_name ?? '',
    last_name: cust.last_name,
    addr_line1: cust.addr_line1 ?? '',
    addr_line2: cust.addr_line2 ?? '',
    addr_line3: cust.addr_line3 ?? '',
    addr_state_cd: cust.addr_state_cd ?? '',
    addr_country_cd: cust.addr_country_cd ?? '',
    addr_zip: cust.addr_zip ?? '',
    phone_num1: cust.phone_num1 ?? '',
    phone_num2: cust.phone_num2 ?? '',
    ssn: cust.ssn,
    govt_issued_id: cust.govt_issued_id ?? '',
    dob: cust.dob ?? '',
    fico_score: cust.fico_score ?? 0,
  });

  const update = (key: string, value: string | number) => setForm((f) => ({ ...f, [key]: value }));

  const mutation = useMutation({
    mutationFn: () =>
      accountsApi.update(acct.acct_id, {
        account: {
          active_status: form.active_status,
          credit_limit: form.credit_limit,
          cash_credit_limit: form.cash_credit_limit,
          open_date: form.open_date || null,
          expiration_date: form.expiration_date || null,
          reissue_date: form.reissue_date || null,
          group_id: form.group_id || null,
        },
        customer: {
          first_name: form.first_name,
          middle_name: form.middle_name || null,
          last_name: form.last_name,
          addr_line1: form.addr_line1 || null,
          addr_line2: form.addr_line2 || null,
          addr_line3: form.addr_line3 || null,
          addr_state_cd: form.addr_state_cd || null,
          addr_country_cd: form.addr_country_cd || null,
          addr_zip: form.addr_zip || null,
          phone_num1: form.phone_num1 || null,
          phone_num2: form.phone_num2 || null,
          ssn: form.ssn,
          govt_issued_id: form.govt_issued_id || null,
          dob: form.dob || null,
          fico_score: form.fico_score || null,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account', String(acct.acct_id)] });
      toast.success('Account updated successfully');
      onSaved();
    },
    onError: (err) => toast.error(getErrorMessage(err)),
  });

  const cls = "rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full";

  return (
    <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(); }} className="space-y-6">
      <SectionCard title="Account Information">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div><label className="text-xs font-medium text-slate-600">Active Status</label>
            <select value={form.active_status} onChange={(e) => update('active_status', e.target.value)} className={cls}>
              <option value="Y">Active (Y)</option><option value="N">Inactive (N)</option>
            </select></div>
          <div><label className="text-xs font-medium text-slate-600">Credit Limit</label>
            <input type="number" step="0.01" min="0" value={form.credit_limit} onChange={(e) => update('credit_limit', Number(e.target.value))} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Cash Credit Limit</label>
            <input type="number" step="0.01" min="0" value={form.cash_credit_limit} onChange={(e) => update('cash_credit_limit', Number(e.target.value))} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Open Date</label>
            <input type="text" maxLength={10} placeholder="YYYY-MM-DD" value={form.open_date} onChange={(e) => update('open_date', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Expiration Date</label>
            <input type="text" maxLength={10} placeholder="YYYY-MM-DD" value={form.expiration_date} onChange={(e) => update('expiration_date', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Group ID</label>
            <input type="text" maxLength={10} value={form.group_id} onChange={(e) => update('group_id', e.target.value)} className={cls} /></div>
        </div>
      </SectionCard>

      <SectionCard title="Customer Name">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div><label className="text-xs font-medium text-slate-600">First Name *</label>
            <input type="text" maxLength={25} value={form.first_name} onChange={(e) => update('first_name', e.target.value)} className={cls} required /></div>
          <div><label className="text-xs font-medium text-slate-600">Middle Name</label>
            <input type="text" maxLength={25} value={form.middle_name} onChange={(e) => update('middle_name', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Last Name *</label>
            <input type="text" maxLength={25} value={form.last_name} onChange={(e) => update('last_name', e.target.value)} className={cls} required /></div>
        </div>
      </SectionCard>

      <SectionCard title="Address">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div><label className="text-xs font-medium text-slate-600">Address Line 1</label>
            <input type="text" maxLength={50} value={form.addr_line1} onChange={(e) => update('addr_line1', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Address Line 2</label>
            <input type="text" maxLength={50} value={form.addr_line2} onChange={(e) => update('addr_line2', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">City</label>
            <input type="text" maxLength={50} value={form.addr_line3} onChange={(e) => update('addr_line3', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">State (2-letter)</label>
            <input type="text" maxLength={2} value={form.addr_state_cd} onChange={(e) => update('addr_state_cd', e.target.value.toUpperCase())} className={`${cls} uppercase`} /></div>
          <div><label className="text-xs font-medium text-slate-600">ZIP Code</label>
            <input type="text" maxLength={10} value={form.addr_zip} onChange={(e) => update('addr_zip', e.target.value)} className={cls} /></div>
        </div>
      </SectionCard>

      <SectionCard title="Contact & Identity">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <div><label className="text-xs font-medium text-slate-600">Phone 1 — (999)999-9999</label>
            <input type="text" maxLength={13} placeholder="(999)999-9999" value={form.phone_num1} onChange={(e) => update('phone_num1', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Phone 2</label>
            <input type="text" maxLength={13} placeholder="(999)999-9999" value={form.phone_num2} onChange={(e) => update('phone_num2', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">SSN (9-digit)</label>
            <input type="text" maxLength={9} value={form.ssn} onChange={(e) => update('ssn', Number(e.target.value))} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Date of Birth</label>
            <input type="text" maxLength={10} placeholder="YYYY-MM-DD" value={form.dob} onChange={(e) => update('dob', e.target.value)} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">FICO Score (300-850)</label>
            <input type="number" min={300} max={850} value={form.fico_score} onChange={(e) => update('fico_score', Number(e.target.value))} className={cls} /></div>
          <div><label className="text-xs font-medium text-slate-600">Govt. Issued ID</label>
            <input type="text" maxLength={20} value={form.govt_issued_id} onChange={(e) => update('govt_issued_id', e.target.value)} className={cls} /></div>
        </div>
      </SectionCard>

      <div className="flex justify-end gap-3">
        <button type="button" onClick={onCancel} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
          <X className="h-4 w-4" /> Cancel
        </button>
        <button type="submit" disabled={mutation.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60">
          {mutation.isPending && <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
          <Save className="h-4 w-4" /> Save Changes
        </button>
      </div>
    </form>
  );
}

export default function AccountDetailPage({ params }: { params: Promise<{ acctId: string }> }) {
  const { acctId } = use(params);
  const [isEditing, setIsEditing] = useState(false);
  const router = useRouter();

  const { data, isLoading, error } = useQuery({
    queryKey: ['account', acctId],
    queryFn: async () => {
      const response = await accountsApi.get(acctId);
      return response.data as AccountWithCustomer;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" label="Loading account..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 p-6 text-center">
        <p className="text-sm text-red-700 font-medium">
          {error ? getErrorMessage(error) : 'Account not found'}
        </p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-blue-600 hover:underline">Go back</button>
      </div>
    );
  }

  const acct = data.account;
  const cust = data.customer;

  return (
    <div>
      <PageHeader
        title={`Account #${acct.acct_id}`}
        description={`${cust.first_name} ${cust.last_name}`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: `Account ${acct.acct_id}` },
        ]}
        actions={
          <div className="flex gap-2">
            <Link href={`/cards?account_id=${acct.acct_id}`} className="px-3 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
              View Cards
            </Link>
            {!isEditing && (
              <button onClick={() => setIsEditing(true)} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors">
                <Edit2 className="h-4 w-4" /> Edit
              </button>
            )}
          </div>
        }
      />

      {isEditing ? (
        <EditForm data={data} onCancel={() => setIsEditing(false)} onSaved={() => setIsEditing(false)} />
      ) : (
        <div className="space-y-6">
          <SectionCard title="Account Summary">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5">
              <ReadonlyField label="Status" value={<Badge variant={statusBadge(acct.active_status)} label={acct.active_status === 'Y' ? 'Active' : 'Inactive'} />} />
              <ReadonlyField label="Current Balance" value={formatCurrency(acct.curr_bal)} />
              <ReadonlyField label="Credit Limit" value={formatCurrency(acct.credit_limit)} />
              <ReadonlyField label="Cash Credit Limit" value={formatCurrency(acct.cash_credit_limit)} />
              <ReadonlyField label="Open Date" value={acct.open_date} />
              <ReadonlyField label="Expiration Date" value={acct.expiration_date} />
              <ReadonlyField label="Reissue Date" value={acct.reissue_date} />
              <ReadonlyField label="Group ID" value={acct.group_id} />
              <ReadonlyField label="Cycle Credit" value={formatCurrency(acct.curr_cycle_credit)} />
              <ReadonlyField label="Cycle Debit" value={formatCurrency(acct.curr_cycle_debit)} />
            </div>
          </SectionCard>

          <SectionCard title="Customer Information">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-5">
              <ReadonlyField label="Customer ID" value={cust.cust_id} />
              <ReadonlyField label="First Name" value={cust.first_name} />
              <ReadonlyField label="Middle Name" value={cust.middle_name} />
              <ReadonlyField label="Last Name" value={cust.last_name} />
              <ReadonlyField label="Date of Birth" value={cust.dob} />
              <ReadonlyField label="FICO Score" value={cust.fico_score} />
            </div>
          </SectionCard>

          <SectionCard title="Address">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-5">
              <ReadonlyField label="Line 1" value={cust.addr_line1} />
              <ReadonlyField label="Line 2" value={cust.addr_line2} />
              <ReadonlyField label="City" value={cust.addr_line3} />
              <ReadonlyField label="State" value={cust.addr_state_cd} />
              <ReadonlyField label="Country" value={cust.addr_country_cd} />
              <ReadonlyField label="ZIP" value={cust.addr_zip} />
            </div>
          </SectionCard>

          <SectionCard title="Contact">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-5">
              <ReadonlyField label="Phone 1" value={cust.phone_num1} />
              <ReadonlyField label="Phone 2" value={cust.phone_num2} />
              <ReadonlyField label="SSN" value={cust.ssn ? `***-**-${String(cust.ssn).slice(-4)}` : '—'} />
              <ReadonlyField label="Govt. ID" value={cust.govt_issued_id} />
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}
