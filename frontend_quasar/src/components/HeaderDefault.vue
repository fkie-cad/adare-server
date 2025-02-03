<template>
    <q-header
      elevated
      class="bg-primary text-white"
    >
      <q-toolbar
        class="q-pr-none"
      >

        <q-toolbar-title>Adare Web</q-toolbar-title>

        <q-tabs
          v-model="tab"
          inline-label
          active-bg-color="brand"
          class="q-pr-md"
        >
          <q-route-tab
            name="home"
            label="Home"
            icon="home"
            to="/home"
            v-if="isLoggedIn"
          />
          <q-route-tab
            name="run"
            label="Runs"
            icon="directions_run"
            to="/run"
            v-if="isLoggedIn"
          />
          <q-route-tab
            name="experiment"
            icon="science"
            label="Experiments"
            to="/experiment"
            v-if="isLoggedIn"
          />
          <q-route-tab
            name="environment"
            icon="terrain"
            label="Environments"
            to="/environment"
            v-if="isLoggedIn"
          />
          <q-route-tab
            name="request"
            icon="ion-git-pull-request"
            label="Requests"
            to="/request"
            v-if="isLoggedIn"
          />
          <q-route-tab
            name="testfunctionset"
            icon="hive"
            label="Testfunctionsets"
            to="/testfunctionset"
            v-if="isLoggedIn"
          />
        </q-tabs>

        <div v-if="!isLoggedIn" class="full-height">
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
        <div v-if="isLoggedIn && profile" class="full-height">
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
                  {{ profile.user.username }}
                </span>
              </template>
              <div class="row no-wrap q-pa-md">
                <div class="column  justify-center items-center q-pa-lg">
                  <ProfileImage
                    :profile="profile"
                    size="lg"
                  />
                  <div class="text-subtitle1 tex q-mt-md">{{ profile.user.username }}</div>
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
import { useLoginStore } from 'src/store/login';
import { useUserStore } from 'src/store/user';
import {onMounted, ref, computed} from 'vue';
import ProfileImage from 'components/ProfileImage.vue';
import {useRouter} from 'vue-router';

export default {
  name: 'HeaderDefault',
  components: {
    ProfileImage
  },

  setup(){
    const router = useRouter()
    const loginStore = useLoginStore()
    const userStore = useUserStore()

    const isLoggedIn = computed(() => loginStore.isLoggedIn)
    const profile = computed(() => userStore.loggedInUserProfile)

    async function logout(){
      loginStore.logout()
      userStore.clearUserProfiles()
      await router.push('/login')
    }

    onMounted(async () => {
      await userStore.loadLoggedInUserProfile()
    })

    return {
      isLoggedIn,
      profile,
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
