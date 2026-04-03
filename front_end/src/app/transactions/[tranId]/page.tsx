import TransactionViewScreen from "./TransactionViewScreen";

interface Props {
  params: { tranId: string };
}

export default function TransactionDetailPage({ params }: Props) {
  return <TransactionViewScreen initialTranId={params.tranId} />;
}
