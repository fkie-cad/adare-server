import { boot } from 'quasar/wrappers'
import OptionalRouterLink from 'components/global/OptionalRouterLink.vue';
import AdvancedDataTable from 'components/global/AdvancedDataTable.vue';

// "async" is optional;
// more info on params: https://v2.quasar.dev/quasar-cli/boot-files
export default boot(async ({app}) => {
  // something to do
  app.component('optional-router-link', OptionalRouterLink);
  app.component('AdvancedDataTable', AdvancedDataTable);

})
