/**
 * Account Update page — COACTUPC / CACTUPA screen.
 *
 * Client component: wraps the AccountUpdateForm which drives the
 * full COACTUPC state machine (fetch → edit → confirm → save).
 */

import { AccountUpdateClient } from "@/components/forms/AccountUpdateClient";

interface Props {
  params: { acctId: string };
}

export default function AccountUpdatePage({ params }: Props) {
  return <AccountUpdateClient acctId={params.acctId} />;
}
