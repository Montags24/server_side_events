<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useEventSource } from "@vueuse/core";

type Item = {
  id: number;
  title: string;
  created_at: string;
};

type Notification = {
  id: number;
  message: string;
  created_at: string;
};

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const items = ref<Item[]>([]);
const notifications = ref<Notification[]>([]);
const title = ref("");
const notificationMessage = ref("");
const error = ref("");

const { data } = useEventSource(`${apiBaseUrl}/notifications/stream`);

async function loadItems() {
  error.value = "";

  try {
    const response = await fetch(`${apiBaseUrl}/items`);

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    items.value = await response.json();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unable to load items";
  }
}

async function createItem() {
  const trimmedTitle = title.value.trim();

  if (!trimmedTitle) {
    return;
  }

  error.value = "";

  try {
    const response = await fetch(`${apiBaseUrl}/items`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ title: trimmedTitle })
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    title.value = "";
    await loadItems();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Unable to create item";
  }
}

async function loadNotifications() {
  try {
    const response = await fetch(`${apiBaseUrl}/notifications`);

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    notifications.value = await response.json() as Notification[];
  } catch (err) {
    console.error("Unable to load notifications:", err instanceof Error ? err.message : err);
  }
}

async function createNotification() {
  const trimmedMessage = notificationMessage.value.trim();

  if (!trimmedMessage) {
    return;
  }

  try {
    const response = await fetch(`${apiBaseUrl}/notifications`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ message: trimmedMessage })
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    notificationMessage.value = "";
  } catch (err) {
    console.error("Unable to create notification:", err instanceof Error ? err.message : err);
  }
}

function addNotification(notification: Notification) {
  const alreadyLoaded = notifications.value.some(
    (existingNotification) => existingNotification.id === notification.id
  );

  if (!alreadyLoaded) {
    notifications.value.unshift(notification);
  }
}

watch(data, (newData) => {
  if (newData) {
    try {
      const notification = JSON.parse(newData) as Notification;
      addNotification(notification);
    } catch (err) {
      console.error("Failed to parse notification:", err instanceof Error ? err.message : err);
    }
  }
});

onMounted(() => {
  loadItems();
  loadNotifications();
});
</script>

<template>
  <main class="app-shell">
    <section class="panel">
      <h1>Learning App</h1>

      <form class="item-form" @submit.prevent="createItem">
        <label for="title">Item title</label>
        <div class="form-row">
          <input id="title" v-model="title" type="text" placeholder="Add a test item" />
          <button type="submit">Add</button>
        </div>
      </form>

      <p v-if="error" class="error">{{ error }}</p>

      <ul class="item-list">
        <li v-for="item in items" :key="item.id">
          <span>{{ item.title }}</span>
          <time>{{ item.created_at }}</time>
        </li>
      </ul>
    </section>
    <section class="panel">
      <h2>Notifications</h2>

      <form class="item-form" @submit.prevent="createNotification">
        <label for="notification-message">Notification message</label>
        <div class="form-row">
          <input id="notification-message" v-model="notificationMessage" type="text"
            placeholder="Broadcast a notification" />
          <button type="submit">Send</button>
        </div>
      </form>

      <ul class="item-list">
        <li v-for="notification in notifications" :key="notification.id">
          <span>{{ notification.message }}</span>
          <time>{{ notification.created_at }}</time>
        </li>
      </ul>
    </section>
  </main>
</template>
