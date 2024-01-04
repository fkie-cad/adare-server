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

export default {
  'name': 'OauthRedirect',

  setup() {
    const route = useRoute();
    const router = useRouter();

    // Access query parameters
    const state = computed(() => route.query.state);
    const code = computed(() => route.query.code);

    // Redirect to login page if no state or code is provided
    if (!state.value || !code.value) {
      console.log('No state or code provided');
        // router.push('/login');
    }

    // send a post request to the oauth backend to get the access token
    const getAccessToken = async () => {
      axios.defaults.withCredentials = true;
      const response = await axios.post(API_URLS.GITEA_OAUTH_API+`?state=${state.value}&code=${code.value}`);
      return response.data.access;
    };

    onMounted(async () => {
      // get the access token
      const accessToken = await getAccessToken();
      // save the access token in the local storage
      console.log(accessToken)
    });

  }
}
</script>
