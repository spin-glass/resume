function CurrentDate() {
  const currentDate = new Date();
  const formattedDate = new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(currentDate);

  return (
    <div className="mt-2 text-right font-bold rounded px-6 py-2 m-1 transition duration-150 ease-in-out">
        {formattedDate}
    </div>
  );
}

export default CurrentDate
