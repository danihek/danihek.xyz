document.addEventListener("DOMContentLoaded", function() {
  // Fetch the content of the text file
  fetch('article.txt')
    .then(response => response.text())
    .then(articleContent => {
      // Split the content into lines
      const lines = articleContent.split('\n');

      // The first line is assumed to be the title
      const title = lines[0];
      document.getElementById('article-title').innerText = title;

      // The rest of the lines are the content
      const content = lines.slice(1).join('<br>');
      document.getElementById('article-content').innerHTML = formatText(content);
    })
    .catch(error => {
      console.error('Error fetching article:', error);
    });
});
// ...
function formatText(text) {
        text = text.replace(/\*\*\*(.*?)\*\*\*/g, '<span class="bold cursive">$1</span>');
        text = text.replace(/\*\*(.*?)\*\*/g, '<span class="bold">$1</span>');
        text = text.replace(/\*(.*?)\*/g, '<span class="cursive">$1</span>');
        text = text.replace(/-/g, '·');

        return text;
    }
