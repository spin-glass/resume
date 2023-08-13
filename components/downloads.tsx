function DownloadButton() {
  return (
    <div className="flex justify-end mt-20">
    <div>
    <a
      href="/resume-ja.pdf"
      download
      className="bg-gray-300 hover:bg-gray-400 text-black font-bold rounded px-6 py-2 m-1 transition duration-150 ease-in-out"
    >
      pdf
    </a>
    </div>
    </div>
  );
}

export default function Downloads() {
  return <DownloadButton />;
}
