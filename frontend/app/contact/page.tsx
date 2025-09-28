export default function ContactPage() {
  return (
    <div className="prose">
      <h1>Контакты / Опубликовать статью</h1>
      <p>
        Если вы хотите опубликовать статью, пожалуйста, отправьте материал на почту
        {' '}<a href="mailto:email@example.com">email@example.com</a> со следующей информацией:
      </p>
      <ul>
        <li>Заголовок</li>
        <li>Имя автора</li>
        <li>Полный текст (можно в формате HTML/Markdown) и изображения</li>
        <li>Контакт для связи</li>
      </ul>
    </div>
  );
}


