
const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const $ = id => document.getElementById(id);
const KEY = "nomer_x_launcher_v1";

let state;
try {
  state = JSON.parse(localStorage.getItem(KEY)) || {};
} catch {
  state = {};
}

let balance = Number(state.balance) || 0;
let history = Array.isArray(state.history) ? state.history : [];
let current = history.find(x => !x.sold) || null;
let busy = false;

function save() {
  localStorage.setItem(KEY, JSON.stringify({ balance, history }));
}

function money(n) {
  return n.toLocaleString("ru-RU") + " сум";
}

function renderBalance() {
  $("balance").textContent = balance.toLocaleString("ru-RU");
}

function generateNumber() {
  const region = ["01", "10", "20", "30", "40", "50", "60", "70", "75", "80", "85", "90"][Math.floor(Math.random() * 12)];
  const letters = "ABCEHKMOPTX";
  const letter = () => letters[Math.floor(Math.random() * letters.length)];

  let digits = String(Math.floor(Math.random() * 1000)).padStart(3, "0");
  const roll = Math.random();

  if (roll < .05) digits = "777";
  else if (roll < .10) digits = "888";
  else if (roll < .15) digits = "999";
  else if (roll < .20) digits = "001";
  else if (roll < .25) digits = "007";
  else if (roll < .30) digits = "555";

  return `${region} ${letter()} ${digits} ${letter()}${letter()}`;
}

function getPrice(number) {
  const digits = number.split(" ")[2];
  const letters = number.split(" ")[3];

  if (/^(\d)\1\1$/.test(digits)) {
    return { price: 15000000, rarity: "LEGENDARY" };
  }
  if (["007", "001"].includes(digits)) {
    return { price: 8000000, rarity: "RARE" };
  }
  if (["123", "321", "555", "777", "888", "999"].includes(digits)) {
    return { price: 5000000, rarity: "RARE" };
  }
  if (digits[0] === digits[1] ||
      digits[1] === digits[2] ||
      letters[0] === letters[1]) {
    return { price: 2000000, rarity: "UNCOMMON" };
  }
  return { price: 500000, rarity: "COMMON" };
}

function displayCurrent(item) {
  $("number").textContent = item.number;
  $("price").textContent = money(item.price);
  $("rarity").textContent = item.rarity;
  $("sell").disabled = item.sold;
}

function renderHistory() {
  const box = $("history");
  box.innerHTML = "";
  $("count").textContent = history.length + " номеров";

  if (!history.length) {
    box.innerHTML = '<div class="empty">Твои номера появятся здесь</div>';
    return;
  }

  history.slice(0, 10).forEach(item => {
    const row = document.createElement("div");
    row.className = "item";

    const left = document.createElement("div");
    const number = document.createElement("strong");
    number.textContent = item.number;

    const status = document.createElement("small");
    status.textContent = item.sold ? "✓ Продан" : "Не продан";
    left.append(number, status);

    const right = document.createElement("div");
    right.className = "amount";
    right.textContent = money(item.price);

    row.append(left, right);
    box.appendChild(row);
  });
}

$("spin").addEventListener("click", () => {
  if (busy) return;
  busy = true;
  $("spin").disabled = true;
  $("sell").disabled = true;
  $("rarity").textContent = "НОМЕР КРУТИТСЯ...";
  $("plate").classList.add("rolling");

  let count = 0;
  const timer = setInterval(() => {
    $("number").textContent = generateNumber();
    count++;

    if (count >= 15) {
      clearInterval(timer);

      const number = generateNumber();
      const info = getPrice(number);

      current = {
        id: Date.now(),
        number,
        price: info.price,
        rarity: info.rarity,
        sold: false,
        date: new Date().toLocaleString("ru-RU")
      };

      history.unshift(current);
      history = history.slice(0, 100);

      $("plate").classList.remove("rolling");
      displayCurrent(current);
      renderHistory();
      save();

      $("spin").disabled = false;
      busy = false;
    }
  }, 90);
});

$("sell").addEventListener("click", () => {
  if (!current || current.sold || busy) return;

  current.sold = true;
  balance += current.price;

  $("rarity").textContent = "НОМЕР ПРОДАН";
  $("sell").disabled = true;

  renderBalance();
  renderHistory();
  save();
});

renderBalance();
renderHistory();

if (current) displayCurrent(current);
