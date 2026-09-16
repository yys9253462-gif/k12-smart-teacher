const form = document.querySelector('#grader');
const status = document.querySelector('#status');
const result = document.querySelector('#result');
const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
form.addEventListener('submit', async (event) => {
  event.preventDefault(); result.hidden = true; status.textContent = '正在识别并批改，请稍候…';
  const button = document.querySelector('#submit'); button.disabled = true;
  try {
    const response = await fetch('/api/grade', {method:'POST', body:new FormData(form)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '批改失败');
    const questions = data.questions.map(q => `<article class="question"><span class="badge">${escapeHtml(q.status)}</span> <strong>${escapeHtml(q.number)} · ${escapeHtml(q.score)}</strong><p><b>题目：</b>${escapeHtml(q.question)}</p><p><b>学生答案：</b>${escapeHtml(q.student_answer)}</p><p><b>批改依据：</b>${escapeHtml(q.reason)}</p><p><b>讲解：</b>${escapeHtml(q.explanation)}</p><small>模型置信度：${Math.round((Number(q.confidence)||0)*100)}%</small></article>`).join('');
    result.innerHTML = `<h2>${escapeHtml(data.subject)} · ${escapeHtml(data.grade)}</h2><p>${escapeHtml(data.overview)}</p>${questions}<h3>薄弱知识点</h3><p>${data.weak_points.map(escapeHtml).join('、') || '暂无'}</p><h3>下一步</h3><ul>${data.next_steps.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ul><p class="notice"><b>人工复核提示：</b>${escapeHtml(data.caution)}</p>`;
    result.hidden = false; status.textContent = '批改完成。请先复核“需人工确认”或低置信度题目。';
  } catch (error) { status.textContent = `批改失败：${error.message}`; }
  finally { button.disabled = false; }
});
