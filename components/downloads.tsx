function DownloadButton() {
  return (
    <>
      <a
        href="/resume-ja.pdf"
        download
        className="bg-gray-300 hover:bg-blue-100 text-white rounded px-4 py-2 m-1 w-5"
      >
        日本語
      </a>
      <a
        href="resume-en.pdf"
        download
        className="bg-gray-300 hover:bg-blue-100 text-white rounded px-4 py-2 m-1 w-5"
      >
        English
      </a>
    </>
  );
}

export default function Downloads() {
  return <DownloadButton />;
}
