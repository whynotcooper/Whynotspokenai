/* 主题切换 */
const themeToggle = document.getElementById('themeToggle');
themeToggle.addEventListener('click', () => {
  const isDark = document.body.dataset.theme === 'dark';
  document.body.dataset.theme = isDark ? '' : 'dark';
  localStorage.setItem('theme', isDark ? '' : 'dark');
});
// 恢复上次主题
document.body.dataset.theme = localStorage.getItem('theme') || '';

/* 搜索联想 */
const keywords = [
  '托福口语 Task 1', '雅思 Part 2 话题卡', 'AI 纠音',
  '地道俚语', '旅游对话', '学术交流场景'
];
const searchInput = document.getElementById('searchInput');
const suggestionBox = document.getElementById('suggestionBox');

function toggleSuggestion(show){
  suggestionBox.style.display = show ? 'block' : 'none';
}

function renderSuggestions(list){
  suggestionBox.innerHTML = '';
  list.forEach(text => {
    const li = document.createElement('li');
    li.textContent = text;
    li.addEventListener('click', () => {
      searchInput.value = text;
      toggleSuggestion(false);
    });
    suggestionBox.appendChild(li);
  });
}

searchInput.addEventListener('input', () => {
  const val = searchInput.value.trim().toLowerCase();
  if (!val) { toggleSuggestion(false); return; }
  const matches = keywords.filter(k => k.toLowerCase().includes(val));
  renderSuggestions(matches);
  toggleSuggestion(matches.length > 0);
});

document.addEventListener('click', e => {
  if (!e.target.closest('.search-box')) toggleSuggestion(false);
});