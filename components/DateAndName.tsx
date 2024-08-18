import { useState, useEffect } from 'react';

function DateDisplay() {
  const [currentText, setCurrentText] = useState('Current');

  useEffect(() => {
    // クライアントサイドでのみ実行されるため、サーバーサイドレンダリング時のエラーを防ぐ
    if (navigator.language.startsWith('ja')) {
      setCurrentText('現在');
    }
  }, []); // 空の依存配列で、初回レンダリング時にのみ実行

  const currentDate = new Date();
  const formattedDate = new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(currentDate);

  return (
    <div className="mt-2 text-right font-bold rounded px-6 py-2 m-1 transition duration-150 ease-in-out">
        {formattedDate} {currentText}
    </div>
  );
}

export default DateDisplay;
