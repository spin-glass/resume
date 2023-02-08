// Example from https://beta.reactjs.org/learn

import { useState } from 'react'
import styles from './counters.module.css'

function DownloadButton() {
  const [count, setCount] = useState(0)

  function handleClick() {
    setCount(count + 1)
  }

  return (
    <>
      <div>
      <h1>Language</h1>
      <button className={styles.counter}>
        <a href="./ja">日本語</a>
      </button>
      <button className={styles.counter}>
      <a href="./en">English</a>
      </button>
      </div>
      <div>
      <h1>Downloads</h1>
      <button className={styles.counter}>
        <a href="https://drive.google.com/file/d/1avUou44qwDvrk0ioTU2SLMQ9fV4PSvrl/view?usp=share_link" download="resume-ja.pdf">職務経歴書(日本語)</a>
      </button>
      <button className={styles.counter}>
      <a href="https://drive.google.com/file/d/1hnU7-Ndp0Tj7oRmYJkKRqdK56C8g91yh/view?usp=share_link" download="resume-ja.pdf">Resume(English)</a>
      </button>
      </div>
    </>
  )
}

export default function Downloads() {
  return <DownloadButton />
}
