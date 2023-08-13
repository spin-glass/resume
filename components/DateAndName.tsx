function DateDisplay() {
  const currentDate = new Date();
  const formattedDate = new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(currentDate);

  return (
    <div className="mt-2 text-right text-black font-bold rounded px-6 py-2 m-1 transition duration-150 ease-in-out">
        {formattedDate}現在
    </div>
  );
}

function NameDisplay({ name }) {
  return (
    <div className="mt-2 text-right text-black font-bold rounded px-6 py-2 m-1 transition duration-150 ease-in-out">
        {name}
    </div>
  );
}

export default function DateAndName({ name }){
  return (
    <div className="mt-20">
      <DateDisplay />
      <NameDisplay name={name} />
    </div>
  );
}
