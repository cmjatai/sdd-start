<template>
  <div class="emf-raw-data-viewer">
    <ul class="nav nav-tabs">
      <li
        class="nav-item"
        v-for="rawdatafile in state.rawdatafileList"
        :key="`rdf-item-${rawdatafile.id}`"
        @click="state.rawdatafile_selected = rawdatafile"
      >
        <a
          :class="{ 'active': state.rawdatafile_selected && state.rawdatafile_selected.id === rawdatafile.id, 'nav-link': true }"
        >
          {{ rawdatafile.nome_arquivo }}
        </a>
      </li>
    </ul>
    <raw-data-file-viewer
      v-if="state.rawdatafile_selected"
      :rdf="state.rawdatafile_selected"
      :key="`rdfv-${state.rawdatafile_selected.id}`"
    />
  </div>
</template>
<script setup>
import { onMounted, reactive, defineProps } from 'vue'
import RawDataFileViewer from './RawDataFileViewer.vue'

import Utils from '~@/js/resources'

const props = defineProps({
  rawdata: {
    type: Number,
    required: true
  },
})

const state = reactive({
  rawdatafileList: [],
  rawdatafile_selected: null,
})

onMounted(() => {
  const rawdata = props.rawdata
  Utils.Utils.getModelOrderedList(
    'etl', 'rawdatafile', 'sequencia', 1, `&rawdata=${rawdata}&page_size=1000`
  ).then((response) => {
    state.rawdatafileList = response.data.results
    if (state.rawdatafileList.length > 0) {
      state.rawdatafile_selected = state.rawdatafileList[0]
    }
  }).catch((error) => {
    console.error('Error fetching raw data file:', error)
  })
})
</script>

<style scoped lang="scss">
  .emf-raw-data-viewer {
    margin: 0 -1rem;
    margin-bottom: -1rem;
    overflow-x: auto;
    display: flex;
    flex-direction: column;
    .nav {
      padding-left: 1rem;
      padding-right: 1rem;
      flex-wrap: nowrap;
      .nav-item {
        .nav-link {
          padding: 5px;
          line-height: 1;
          cursor: pointer;
        }
      };
    }
  }
  @media screen and (min-width: 1200px) {
    .emf-raw-data-viewer {
      margin: 0 -2rem;
      margin-bottom: -2rem;
      .nav {
        padding-left: 2rem;
        padding-right: 2rem;
      }
      .nav-item {
        .nav-link {
          padding: 10px;
        }
      };
    }
  }
</style>
style
