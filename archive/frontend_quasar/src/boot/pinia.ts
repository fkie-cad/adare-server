import { boot } from 'quasar/wrappers';
import { createPinia } from 'pinia';

export default boot(({ app, router }) => {
  const pinia = createPinia();

  // Add router to Pinia so it can be accessed in stores
  pinia.use(() => ({ router }));

  // Register Pinia with the Vue app
  app.use(pinia);
});
