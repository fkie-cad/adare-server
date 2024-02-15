<template>
  <router-link :to="vars.formatter(row[vars.field])">
    <q-icon
      :name="vars.icon"
      size="32px"
      :color="vars.color"
      class="custom-hover-icon"
    />
  </router-link>
</template>

<script lang="ts">
import { CustomQTableColumn, TypeVarsDetails} from 'src/datatypes/quasar_extensions';

const defaultTypeVarsDetails: TypeVarsDetails = {
  icon: 'o_add_cirlce',
  formatter: (field_name: string | undefined) => {
    if (!field_name) {
      return '';
    }
    return '/' + field_name;
  },
  field: 'uuid',
  color: 'secondary',
};

export default {
  name: 'DataTableDetails',
  components: { },
  props: {
    data: {
      type: Object,
      required: false,
    },
    row: {
      type: Object,
      required: true,
    },
    col: {
      type: Object as () => CustomQTableColumn,
      required: true,
    },
  },

  setup(props) {
    const vars = Object.assign({}, defaultTypeVarsDetails, props.col.typeVarsDetails);
    return {
      vars,
    };
  }
};
</script>
