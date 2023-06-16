<template>
    <q-header
      elevated
      class="bg-primary text-white"
    >
      <q-toolbar
        class="q-pr-none"
      >

        <q-toolbar-title> Adare Web </q-toolbar-title>

        <q-tabs
          v-model="tab"
          inline-label
          active-bg-color="brand"
          class="q-pr-md"
        >
          <q-route-tab
            name="home"
            icon="home"
            label="Home"
            to="/"
          />
          <q-route-tab
            name="experiments"
            icon="science"
            label="Experiments"
            to="/experiments"
          />
          <q-route-tab
            name="search"
            icon="search"
            label="Search"
            to="/search"
          />
        </q-tabs>

        <div v-if="!IsLoggedIn" class="full-height">
          <q-btn
              color="white"
              dense
              text-color="primary"
              class="q-ma-xs"
              style="font-weight: bold"
              size="md"
              label="Login"
              icon="login"
              to="/login"
          >
          </q-btn>
        </div>
        <div v-if="IsLoggedIn" class="full-height">
            <q-btn-dropdown
              color="white"
              dense
              text-color="primary"
              class="q-ma-xs"
              size="md"
              dropdown-icon="more_vert"
              icon="person"
            >
              <template v-slot:label>
                <span style="font-size: 14px; font-weight: bold">
                  {{ LoginStore.GetLoginUser }}
                </span>
              </template>
              <div class="row no-wrap q-pa-md">
                <div class="column  justify-center items-center q-pa-lg">
                  <ProfileImage
                    :update_profile_information="update_profile_information"
                  />
                  <div class="text-subtitle1 tex q-mt-md">{{ LoginStore.GetLoginUser }}</div>
                </div>
                <q-separator vertical inset class="q-mx-lg" />
                <div class="column justify-center">
                  <q-btn
                    color="primary"
                    label="Profile"
                    push
                    size="md"
                    v-close-popup
                    class="q-ma-sm"
                    icon="manage_accounts"
                    to="/profile"
                  />
                  <q-btn
                    color="primary"
                    label="Logout"
                    push
                    size="md"
                    v-close-popup
                    class="q-ma-sm"
                    icon="logout"
                    @click="logout"
                  />
                </div>
              </div>
            </q-btn-dropdown>
        </div>


      </q-toolbar>
    </q-header>
</template>

<script>
import { useLoginStore } from 'stores/login';
import { useUserStore } from 'stores/user';
import {ref} from 'vue';
import {storeToRefs} from 'pinia';
import ProfileImage from 'components/ProfileImage.vue';
import {useRouter} from 'vue-router';

export default {
  name: 'HeaderDefault',
  components: {
    ProfileImage
  },

  setup(){
    const LoginStore = useLoginStore()
    const {IsLoggedIn} = storeToRefs(LoginStore)

    const UserStore = useUserStore()
    storeToRefs(UserStore)

    const router = useRouter()

    async function logout(){
      LoginStore.Logout()
      UserStore.ResetUser()
      await router.push('/login')
    }

    return {
      LoginStore,
      IsLoggedIn,
      logout,
      tab: ref('home'),
    }

  }
}
</script>

<style scoped>
.text-brand {
  color: #00A482 !important;
}
.bg-brand {
  background: #00A482 !important;
}
</style>
