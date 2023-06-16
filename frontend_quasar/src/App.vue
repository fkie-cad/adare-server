<template>
  <router-view />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useLoginStore } from 'stores/login';
import 'src/plugins/axios_csrf_intercept';

export default defineComponent({
  name: 'App',

  mounted() {
    let store = useLoginStore()
    store.InitLogin()
  }
});
</script>

<style lang="scss">
// does not change color and style of router-link
.routerLink {
  text-decoration: none;
  color: inherit;
}
</style>
