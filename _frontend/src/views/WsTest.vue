<template>
  <div class="container">
    <h1>{{ title }}</h1>
    <p>{{ message }}</p>
    <button
      class="btn btn-primary"
      @click="increment"
    >
      {{ count }}
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useMessageStore } from '~@/js/stores/MessageStore'

// Injected dependency
const bus = inject('EventBus')

// Reactive state
const count = ref(1)
const title = ref('WsTest!')
const message = ref('Teste de Componente Vue 3 com Websockets!')
const messageStore = useMessageStore()

// Constantes Locais
const observer = {
  apps: [ 'utils'],
  models: [ 'teste'],
}

// Methods
const increment = () => {
  count.value++
  fetch('/testws/')
    .then(response => response.json())
    .then(data => {
      messageStore.addMessage({
        type: 'success',
        text: `${data.message} ${data.teste.teste}`,
        timeout: 5000
      })
    })
}

// Lifecycle hook
onMounted(() => {
  bus.on('sync-refresh', (message) => {
    if (observer.apps.includes(message.app) && observer.models.includes(message.model)) {
      messageStore.addMessage({
        type: 'info',
        title: 'Sync Refresh! ',
        text: `sync-refresh ${message.id}  ${message.app} ${message.model}`,
        timeout: 5000
      })
    }
  })
})
</script>

<style>
</style>
