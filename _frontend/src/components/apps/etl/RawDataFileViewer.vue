<template>
  <div
    class="raw-data-file-viewer"
    v-if="rdf"
    :key="rdf.id"
  >
    <div class="raw-data-file-viewer-content">
      <table class="table table-borderless table-sm table-striped">
        <thead>
          <tr>
            <th>
              {{ rdf.nome_arquivo }}
            </th>
            <td>
              {{ rdf.metadata.description }} - {{ rdf.__str__ }}
            </td>
          </tr>
          <tr>
            <th>
              Características
            </th>
            <td>
              {{ rdf.metadata.features }}
            </td>
          </tr>
        </thead>
      </table>
      <table class="table table-borderless table-sm table-striped">
        <tbody>
          <tr
            v-for="rawLine in rawLineTable"
            :key="`rl-${rawLine.id}`"
          >
            <td><a :href="`/api/etl/rawline/${rawLine.id}`" target="_blank">{{rawLine.id}}</a></td>
            <td
              v-for="(key_vakue, index) in rawLine.jdata.data"
              :key="`rl-${rawLine.id}-${index}`"
            >
              {{ key_vakue[0] }}: <strong>{{ key_vakue[1] }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
      <div
        class="pagination d-inline-flex justify-content-start gap-3 m-3 p-0"
        v-if="state.rawLineList != undefined && state.rawLineList.pagination && state.rawLineList.pagination.total_entries > 0"
      >
        <b-form-select
          v-model="state.pageSize"
          :options="state.pageSizeOptions"
        />
        <b-pagination
          v-model="state.page"
          :total-rows="state.rawLineList.pagination.total_entries"
          :per-page="state.pageSize"
          :limit="10"
          class="mb-0"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, defineProps, computed, watch } from 'vue';
import Utils from '~@/js/resources'
import _ from 'lodash';

const props = defineProps({
  rdf: {
    type: Object,
    required: true,
  },
})

const state = reactive({
  rawLineList: {},
  pageSize: 100,
  pageSizeOptions: [10, 25, 50, 100],
  page: 1,
})

watch(
  () => state.pageSize,
  (newPageSize) => {
    state.page = 1
    const rdf = props.rdf.id
    Utils.Utils.getModelOrderedList(
      'etl', 'rawline', 'sequencia', 1, `&rawdatafile=${rdf}&page_size=${ newPageSize }`
    ).then((response) => {
      state.rawLineList = response.data

    }).catch((error) => {
      console.error('Error fetching raw data file:', error)
    })
  }
)
watch(
  () => state.page,
  (newPage) => {
    const rdf = props.rdf.id
    Utils.Utils.getModelOrderedList(
      'etl', 'rawline', 'sequencia', newPage, `&rawdatafile=${rdf}&page_size=${ state.pageSize }`
    ).then((response) => {
      state.rawLineList = response.data

    }).catch((error) => {
      console.error('Error fetching raw data file:', error)
    })
  }
)

onMounted(() => {
  const rdf = props.rdf.id
  Utils.Utils.getModelOrderedList(
    'etl', 'rawline', 'sequencia', 1, `&rawdatafile=${rdf}&page_size=${ state.pageSize }`
  ).then((response) => {
    state.rawLineList = response.data

  }).catch((error) => {
    console.error('Error fetching raw data file:', error)
  })
})

const rawLineTable = computed( () => {
  const listTable = _.map(state.rawLineList.results, (item) => {
    const itemHeader = _.map(item.jdata.layout, (itemLayout) => {
      return {
        name: itemLayout.name,
        ord: itemLayout.ord
      }
    })

    item = {
      id: item.id,
      jdata: {
        data: _.map(itemHeader, (itemHeader) => {
          return [itemHeader.name, item.jdata.data[itemHeader.name]]
        }),
      }
    }
    const lastItem = item.jdata.data.pop()
    item.jdata.data.unshift(lastItem)
    return item

  })
  return listTable
})

</script>

<style scoped lang="scss">
  .raw-data-file-viewer {
    //display: flex;
    //min-width: min-content;

    //flex-wrap: nowrap;
    min-height: 50vh;
  }

  .raw-data-file-viewer-content {
    .table {
      margin-bottom: 0;
      th, td {
        vertical-align: middle;
        padding: 0.5rem;
        white-space: nowrap;
      }
      th {
        text-align: center;
      }
    }

  }
</style>
