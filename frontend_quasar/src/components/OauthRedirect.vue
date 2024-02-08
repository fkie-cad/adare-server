<template>
  <div class="flex flex-col items-center justify-center h-screen">
    <q-spinner-gears size="10em" color="primary" />
  </div>
</template>

<script lang="ts">
import axios from 'axios';
import {computed, onMounted} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import API_URLS from 'src/api';
import { useLoginStore } from 'src/stores/login';

export default {
  'name': 'OauthRedirect',

  setup() {
    const route = useRoute();
    const router = useRouter();
    const LoginStore = useLoginStore();

    // Access query parameters
    const state = computed(() => route.query.state);
    const code = computed(() => route.query.code);


    // Redirect to login page if no state or code is provided
    if (!state.value || !code.value) {
      console.log('No state or code provided');
    }

    if (state.value !== localStorage.getItem('state')) {
      console.log('State does not match');
      // return to login page
      router.push('/login');
    }

    // send a post request to the oauth backend to get the access token
    const loginOnBackend = async () => {
      axios.defaults.withCredentials = true;

      // create a html form to send the post request
      if (!code.value) {
        return;
      }
      const form_data = new FormData();
      form_data.append('code', code.value.toString());

      const response = await axios.post(API_URLS.GITEA_OAUTH_API+`?state=${state.value}`, form_data);

      // check response status
      if (response.status !== 200) {
        return;
      }

      LoginStore.SetLoginToken(response.data.user, response.data.token, response.data.expiry);
      await router.push('/profile');

    };

    onMounted(async () => {
      await loginOnBackend();
    });

  }
}
</script>
