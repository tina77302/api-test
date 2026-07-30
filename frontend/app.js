const userList = document.querySelector("#user-list");
const userForm = document.querySelector("#user-form");
const userMessage = document.querySelector("#user-message");
const refreshButton = document.querySelector("#refresh-users");
const chatForm = document.querySelector("#chat-form");
const chatLog = document.querySelector("#chat-log");

function showUserMessage(text, isError = false) {
  userMessage.textContent = text;
  userMessage.classList.toggle("error", isError);
}

function renderUsers(users) {
  userList.replaceChildren(
    ...users.map((user) => {
      const card = document.createElement("article");
      card.className = "user-card";

      const name = document.createElement("strong");
      name.textContent = `#${user.id} ${user.username}`;

      const email = document.createElement("span");
      email.textContent = user.email;

      const age = document.createElement("span");
      age.textContent = user.age == null ? "나이 미입력" : `${user.age}세`;

      card.append(name, email, age);
      return card;
    }),
  );
}

async function loadUsers() {
  refreshButton.disabled = true;
  showUserMessage("사용자를 불러오는 중입니다.");

  try {
    const response = await fetch("/users");
    if (!response.ok) throw new Error("사용자 목록을 가져오지 못했습니다.");
    const users = await response.json();
    renderUsers(users);
    showUserMessage(`사용자 ${users.length}명을 불러왔습니다.`);
  } catch (error) {
    showUserMessage(error.message, true);
  } finally {
    refreshButton.disabled = false;
  }
}

userForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = userForm.querySelector("button");
  const formData = new FormData(userForm);
  const age = formData.get("age");
  const payload = {
    username: formData.get("username"),
    email: formData.get("email"),
    age: age ? Number(age) : null,
  };

  submitButton.disabled = true;
  try {
    const response = await fetch("/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const body = await response.json();
      throw new Error(body.detail?.[0]?.msg ?? "사용자 등록에 실패했습니다.");
    }

    userForm.reset();
    showUserMessage("사용자가 등록되었습니다.");
    await loadUsers();
  } catch (error) {
    showUserMessage(error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});

function addChatBubble(text, type) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${type}`;
  bubble.textContent = text;
  chatLog.append(bubble);
  chatLog.scrollTop = chatLog.scrollHeight;
  return bubble;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const textarea = chatForm.elements.message;
  const submitButton = chatForm.querySelector("button");
  const message = textarea.value.trim();
  if (!message) return;

  addChatBubble(message, "user");
  textarea.value = "";
  submitButton.disabled = true;
  const loadingBubble = addChatBubble("답변을 생성하는 중입니다…", "assistant");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail ?? "채팅 요청에 실패했습니다.");
    loadingBubble.textContent = body.answer;
  } catch (error) {
    loadingBubble.textContent = error.message;
    loadingBubble.classList.add("error");
  } finally {
    submitButton.disabled = false;
    textarea.focus();
  }
});

refreshButton.addEventListener("click", loadUsers);
loadUsers();
