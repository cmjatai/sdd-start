import Error404 from "./views/Error404.vue"
import Alert from "./components/utils/message/Alert.vue"
import App from './App.vue';
import RefreshPage from "./components/utils/RefreshPage.vue";

// emf = Backend Frontend

const rootComponents = {
    'emf-app': App,
    'emf-alert': Alert,
    'emf-error-404': Error404,
    'emf-refresh-page': RefreshPage,
  }

export default rootComponents
