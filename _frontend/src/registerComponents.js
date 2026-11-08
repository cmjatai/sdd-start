import { defineAsyncComponent } from "vue"
import App from './App.vue'

import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome"

// emf = Backend Frontend

const rootComponents = {
    'emf-app': App,
    'emf-error-404': defineAsyncComponent(() => import('~@/views/Error404.vue')),

  }

const globalComponents = {
  FontAwesomeIcon,

  // Para ser utilizado em qualquer componente Vue sem necessidade de importação.
  // O colocado em globalComponents não precisa ser colocado em rootComponents.
  'emf-alert': defineAsyncComponent(() => import('~@/components/utils/message/Alert.vue')),
  'emf-refresh-page': defineAsyncComponent(() => import('~@/components/utils/RefreshPage.vue')),

}
export default {
  rootComponents,
  globalComponents
}
