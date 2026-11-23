<script setup>
defineProps({
  usuario: {
    type: Object,
    required: true,
  },
  clinicaNome: {
    type: String,
    default: 'Agenda Médica',
  },
})

const emit = defineEmits(['sair'])

function rotuloPerfil(perfil) {
  return perfil === 'ADMINISTRADOR' ? 'Administrador' : 'Recepcionista'
}
</script>

<template>
  <header class="navbar bg-base-100 border-b border-base-300 shadow-xs px-4 lg:px-8">
    <div class="flex-1 flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <div>
        <h1 class="text-lg font-bold leading-tight text-base-content">{{ clinicaNome }}</h1>
        <p class="text-xs text-base-content/60">Sistema de Controle de Consultas</p>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <div class="hidden sm:flex flex-col items-end">
        <span class="text-sm font-semibold leading-tight">{{ usuario.nome }}</span>
        <span
          class="badge badge-sm mt-0.5"
          :class="usuario.perfil === 'ADMINISTRADOR' ? 'badge-primary' : 'badge-secondary'"
        >
          {{ rotuloPerfil(usuario.perfil) }}
        </span>
      </div>

      <button type="button" class="btn btn-outline btn-sm gap-1.5" @click="emit('sair')">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Sair
      </button>
    </div>
  </header>
</template>
