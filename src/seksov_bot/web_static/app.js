const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const params = new URLSearchParams(window.location.search);
const devUserId = params.get('telegram_user_id');
const query = new URLSearchParams();
if (tg?.initData) query.set('initData', tg.initData);
if (devUserId) query.set('telegram_user_id', devUserId);

const setText = (id, value) => { document.getElementById(id).textContent = value; };
const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  "'": '&#39;',
  '"': '&quot;',
}[char]));

function renderEmpty(message) {
  document.getElementById('history').innerHTML = `<div class="muted">${escapeHtml(message)}</div>`;
  document.getElementById('batches').innerHTML = '<div class="muted">Партий пока нет.</div>';
}

function render(data) {
  const profile = data.profile || {};
  setText('subtitle', `${profile.displayName || 'Пользователь'} · персональный медицинский журнал`);
  const batch = data.currentBatch;
  if (batch) {
    setText('remaining', batch.remainingMl);
    setText('remainingTotal', `из ${batch.totalMl}`);
    setText('batchBadge', `${batch.remainingPercent}%`);
    setText('batchInfo', `${batch.drugAmount} ${batch.drugUnit} · создана ${batch.createdAt}`);
    document.getElementById('progressFill').style.width = `${batch.remainingPercent}%`;
  }
  const last = data.history?.[0];
  if (last) {
    setText('lastDose', last.volumeMl);
    setText('lastMeta', `${last.injectedAt} · ${last.site}`);
  }
  document.getElementById('history').innerHTML = (data.history || []).map(item => `
    <article class="event">
      <span class="dot"></span>
      <div><strong>${escapeHtml(item.volumeMl)} · ${escapeHtml(item.route)}</strong><small>${escapeHtml(item.injectedAt)} · ${escapeHtml(item.site)}</small></div>
      <span class="badge">${escapeHtml(item.remainingAfterMl)}</span>
    </article>
  `).join('') || '<div class="muted">Записей пока нет.</div>';
  document.getElementById('batches').innerHTML = (data.batches || []).map(item => `
    <article class="batch">
      <div><strong>${escapeHtml(item.remainingMl)} / ${escapeHtml(item.totalMl)}</strong><div class="muted">${escapeHtml(item.drugAmount)} ${escapeHtml(item.drugUnit)} · ${escapeHtml(item.createdAt)}</div></div>
      <span class="badge">${item.isCurrent ? 'активна' : 'завершена'}</span>
    </article>
  `).join('') || '<div class="muted">Партий пока нет.</div>';
}

fetch(`/api/me?${query.toString()}`)
  .then(async response => {
    if (!response.ok) throw new Error((await response.json()).detail || 'Не удалось загрузить данные');
    return response.json();
  })
  .then(render)
  .catch(error => {
    setText('subtitle', error.message);
    renderEmpty('Откройте приложение кнопкой внутри Telegram-бота. Для локальной проверки включите WEB_DEV_MODE=1 и добавьте ?telegram_user_id=ваш_id.');
  });
