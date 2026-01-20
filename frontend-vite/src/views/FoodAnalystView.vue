<script setup lang="ts">
import { onMounted } from "vue";
import FoodAgentChat from "@/components/food-agent/FoodAgentChat.vue";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";
import { toast } from "vue-sonner";

const authStore = useAuthStore();
const router = useRouter();

onMounted(() => {
  // Check authentication
  if (!authStore.isAuthenticated) {
    toast.error("Please login to access Food Analyst Agent");
    router.push("/login");
  }
});
</script>

<template>
  <div class="h-screen">
    <FoodAgentChat />
  </div>
</template>
