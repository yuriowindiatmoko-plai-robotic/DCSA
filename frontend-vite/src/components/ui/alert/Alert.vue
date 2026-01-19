<script setup lang="ts">
import type { HTMLAttributes } from "vue"
import { cn } from "@/lib/utils"
import { alertVariants } from "."

const props = defineProps<{
  class?: HTMLAttributes["class"]
  variant?: "default" | "destructive"
}>()
</script>

<template>
  <div :class="cn(alertVariants({ variant }), props.class)">
    <slot />
  </div>
</template>
