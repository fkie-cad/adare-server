<template>
  <q-card
      class="col-auto"
      v-if="profile"
    >
      <q-card-section
        class="column justify-center items-center bg-teal-2 tw-h-32"
      >
        <ProfileImage
          editable
          offset_classes="tw-top-8"
          size="lg"
          :profile="profile"
        />
      </q-card-section>
      <q-card-section>
        <div class="row justify-between q-pa-sm">
          <div class="column text-h6 tw-text-gray-600 q-pr-xl">
            username
          </div>
          <div class="column text-h6">
            {{ profile.user.username }}
          </div>
        </div>
        <q-separator />
        <div class="row justify-between q-pa-sm">
          <div class="column text-h6 tw-text-gray-600 q-pr-xl">
            email
          </div>
          <div class="column text-h6">
            {{ profile.user.email }}
          </div>
        </div>
        <q-separator />
        <div class="row justify-between q-pa-sm">
          <div class="column text-h6 tw-text-gray-600 q-pr-xl">
            teams
          </div>
          <div class="column">
            <span v-for="role in profile.teams" v-bind:key="role.id" class="tw-rounded q-pa-xs q-ma-xs tw-text-center tw-font-bold tw-border-2" :class="getColorForRole(role.name)">
              {{ role.name }}
            </span>
          </div>
        </div>
        <q-separator />
        <div class="row justify-between q-pa-sm">
          <div class="column text-h6 tw-text-gray-600 q-pr-xl">
            achievements
          </div>
        </div>
<!--        <div class="row justify-evenly">-->
<!--          <AchievementIcon  :image="achiev.iconfile" :description="achiev.description" :count="achiev.count" v-for="achiev in LoggedInUserStore.GetUserAchievements.values()" v-bind:key="achiev.id" />-->
<!--        </div>-->
      </q-card-section>
    </q-card>
</template>

<script lang="ts">
import { useLoginStore} from 'src/store/login';
import ProfileImage from 'components/ProfileImage.vue';
import { computed, ref, PropType } from 'vue';
import { Profile } from 'src/models/experiment';

export default {
  name: 'ProfileCard',
  components: {
    ProfileImage
  },
  props: {
    profile: {
      type: Object as PropType<Profile>,
      required: true,
    },
  },

  setup(){
    const loginStore = useLoginStore()

    const isLoggedIn = computed(
      () => loginStore.isLoggedIn
    )

    let role_color_mapping = ref<{ [key: string]: string }>({
      'Owners': 'bg-black text-white tw-border-gray-700',
      'Supervisor': 'bg-pink-9 text-white tw-border-pink-600',
    })

    function getColorForRole(role: string){
      if (role_color_mapping.value[role]){
        return role_color_mapping.value[role]
      }else{
        return 'bg-amber-5 text-black tw-border-amber-400'
      }
    }


    return {
      isLoggedIn,
      getColorForRole,
    }

  }
}
</script>
