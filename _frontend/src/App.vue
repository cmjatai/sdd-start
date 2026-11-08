<template>
  <slot />
  <DisplayMessage />
  <div
    id="modalApp"
    ref="modalApp"
  />
</template>
<script setup>

// 1. Imports
import DisplayMessage from '~@/components/utils/message/DisplayMessage'
import { useSyncStore } from '~@/js/stores/pinea/SyncStore'
import { useAuthStore } from '~@/js/stores/pinea/AuthStore'
import { ref } from 'vue'

// 2. Composables
const syncStore = useSyncStore()
syncStore.initialize()

const authStore = useAuthStore()
authStore.loginStatus()

// 3. Props & Emits

// 4. State & Refs
const modalApp = ref(null)

// 5. Computed Properties

// 6. Watchers

// 7. Events & Lifecycle Hooks

// 8. Functions

syncStore.registerModels('utils', ['teste'])

</script>
