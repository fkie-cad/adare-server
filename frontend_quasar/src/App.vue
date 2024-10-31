<template>
  <router-view />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useLoginStore } from 'src/store/login';

export default defineComponent({
  name: 'App',

  mounted() {
    let LoginStore = useLoginStore()
    LoginStore.InitLogin()
  },
});
</script>

<style lang="scss">
// does not change color and style of router-link
.routerLink {
  text-decoration: none;
  color: inherit;
}
</style>
