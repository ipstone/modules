#!/usr/bin/env python
"""
Create mutation summary excel from given tsvs
"""
import argparse
import pandas as pd
import os
import errno
import yaml


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def split_multi_value_columns_to_records(df, columns, separator):
    assert(len(columns) > 1)
    split = pd.DataFrame(df[columns[0]].str.split(separator).tolist(), index=df.index).stack()
    split.name = "SPLIT"
    split.index = split.index.droplevel(-1)
    df_split = df.join(pd.DataFrame({c + "_SPLIT": [s for l in
                                                    df[c].str.split(separator).tolist()
                                                    for s in l] for c in
                                     columns}, index=split.index))
    df_split.index = list(range(len(df_split)))
    return df_split


def select_annotations_with_impact(df, impact, select_effect=".*", filter_effect=None, config=None):
    """Get only annotations with given impact. Also exclude genes in blacklist."""
    # check if df is empty
    if len(df) == 0:
        return df

    def merge_impact(muts, sep):
        return pd.Series({"ANN[*].EFFECT_MERGE": sep.join(muts["ANN[*].EFFECT_SPLIT"]),
                             "ANN[*].IMPACT_MERGE": sep.join(muts["ANN[*].IMPACT_SPLIT"]),
                             "ANN[*].HGVS_P_MERGE": sep.join(muts["ANN[*].HGVS_P_SPLIT"]),
                             "ANN[*].HGVS_C_MERGE": sep.join(muts["ANN[*].HGVS_C_SPLIT"]),
                             "ANN[*].GENE_MERGE": sep.join(muts["ANN[*].GENE_SPLIT"])})

    # assume one unique entry per variant in df
    assert(len(df.drop_duplicates("TUMOR_SAMPLE CHROM POS REF ALT".split())) == len(df))
    # reshape df to record format (columns contain | separated values)
    df_split = split_multi_value_columns_to_records(df,
                                                    "ANN[*].GENE ANN[*].HGVS_P ANN[*].HGVS_C ANN[*].EFFECT ANN[*].IMPACT".split(),
                                                    "|")
    # select only variants with given impact/effect and not in the blacklist
    criteria = df_split["ANN[*].IMPACT_SPLIT"].str.match(impact) & \
                df_split["ANN[*].EFFECT_SPLIT"].str.match(select_effect)
    if filter_effect:
        criteria = criteria & ~df_split["ANN[*].EFFECT_SPLIT"].str.match(filter_effect).astype(bool)
    if config and 'gene_blacklist' in config:
        criteria = criteria & ~df_split["ANN[*].GENE_SPLIT"].isin(config['gene_blacklist'])
    df_split = df_split[criteria]
    # merge remaining variants back to | separated values
    imp_sel = df_split.groupby("TUMOR_SAMPLE CHROM POS REF ALT".split()).apply(lambda x: merge_impact(x, "|"))
    if imp_sel.empty:
        return imp_sel
    rv = df.set_index("TUMOR_SAMPLE CHROM POS REF ALT".split()).join(imp_sel,
        how="inner")
    for c in "ANN[*].GENE ANN[*].HGVS_P ANN[*].HGVS_C ANN[*].EFFECT ANN[*].IMPACT".split():
        rv[c] = rv[c + "_MERGE"]
        del rv[c + "_MERGE"]

    return rv.reset_index()


def create_absolute_df(absolute_somatic_txts, absolute_segments):
    absdf = pd.concat([pd.read_csv(asegs, sep="\t", dtype={"Chromosome": str}) for asegs
               in absolute_somatic_txts], ignore_index=True)
    absdf["Chromosome"] = absdf.Chromosome.replace({"23": "X", "24": "Y"})
    absdf["TUMOR_SAMPLE"] = absdf.Sample.apply(lambda x: x.split("_")[0])
    absdf["NORMAL_SAMPLE"] = absdf.Sample.apply(lambda x: x.split("_")[1])
    absdf.drop([c for c in absdf.columns if c not in "TUMOR_SAMPLE NORMAL_SAMPLE Ref Alt Chromosome Position".split()],
                         axis=1,
                         inplace=True)
    absdf.rename(columns={"Ref": "REF", "Alt": "ALT", "Chromosome": "CHROM", "Position": "POS"}, inplace=True)
    abscolumns = "cancer_cell_frac Pr_somatic_clonal ccf_CI95_low".split()
    absegdf = pd.concat([pd.read_csv(f, dtype={"Chromosome": str}, sep="\t") for f in absolute_segments],
                   ignore_index=True)[abscolumns]
    assert(len(absdf) == len(absegdf))
    for c in abscolumns:
        absdf[c] = absegdf[c]
    absdf["clonality"] = absdf.apply(lambda x: "clonal" if x.Pr_somatic_clonal >= .5 or x.ccf_CI95_low >= .9 else "subclonal", axis=1)

    return absdf


def add_maf(df):
    rv = df.copy()
    def f(x):
        if "," in x["TUMOR.AD"] and sum(map(float, x["TUMOR.AD"].split(','))) > 0:
            return float(x["TUMOR.AD"].split(",")[1]) / sum(map(float, x["TUMOR.AD"].split(',')))
        else:
            return float('nan')
    def g(x):
        if "," in x["NORMAL.AD"] and sum(map(float, x["NORMAL.AD"].split(','))) > 0:
            return float(x["NORMAL.AD"].split(",")[1]) / sum(map(float, x["NORMAL.AD"].split(',')))
        else:
            return float('nan')
    if len(df) > 0:
        rv["TUMOR_MAF"] = df.apply(f, axis=1)
        rv["NORMAL_MAF"] = df.apply(g, axis=1)
    else:
        rv["TUMOR_MAF"] = pd.Series()
        rv["NORMAL_MAF"] = pd.Series()
    return rv


def add_dp(df):
    rv = df.copy()
    def h(x):
        if "," in x["TUMOR.AD"]:
            return sum(map(float, x["TUMOR.AD"].split(',')))
        else:
            return float('nan')
    def i(x):
        if "," in x["NORMAL.AD"]:
            return sum(map(float, x["NORMAL.AD"].split(',')))
        else:
            return float('nan')
    if len(df) > 0:
        rv["TUMOR_DP"] = df.apply(h, axis=1)
        rv["NORMAL_DP"] = df.apply(i, axis=1)
    else:
        rv["TUMOR_DP"] = pd.Series()
        rv["NORMAL_DP"] = pd.Series()
    return rv


def add_cancer_gene(df):
    rv = df.copy()
    rv["cancer_gene"] = df.apply(lambda x: "true" if x["cancer_gene_census"] == "true" or
                                 x["kandoth"] == "true" or
                                 x["lawrence"] == "true" else ".",
                                 axis=1)
    rv["num_cancer_gene"] = df.apply(lambda x: sum([x["cancer_gene_census"] == "true",
                                                    x['kandoth'] == 'true',
                                                    x['lawrence'] == 'true']), axis=1)
    return rv


def add_non_existent_columns(df, columns, fill_value):
    rv = df.copy()
    for c in columns:
        if c not in df.columns:
            rv[c] = len(df) * [fill_value]
    return rv


def add_columns_write_excel(df, writer, sheetname, absdf=None, write_columns=None, output_tsv_dir=None, annotdf=None, config=None):
    if all([c in df.columns for c in "TUMOR.AD NORMAL.AD".split()]):
        df = add_maf(df)
        df = add_dp(df)
    if len(df > 0):
        if all([c in df.columns for c in "cancer_gene_census kandoth lawrence".split()]):
            df = add_cancer_gene(df)
        if write_columns:
            df = df[[c for c in write_columns if c in df.columns]]
        df = df.set_index("TUMOR_SAMPLE NORMAL_SAMPLE CHROM POS REF ALT".split())
        if absdf is not None:
            df = df.join(absdf.set_index("TUMOR_SAMPLE NORMAL_SAMPLE CHROM POS REF ALT".split()), how='left')
        if annotdf is not None:
            df = df.join(annotdf.set_index("TUMOR_SAMPLE NORMAL_SAMPLE CHROM POS REF ALT".split()), how='left')
        df = df.reset_index()
        if config is not None and 'sample_rename' in config:
            for k in config['sample_rename']:
                df['TUMOR_SAMPLE'] = df['TUMOR_SAMPLE'].str.replace(k, config['sample_rename'][k])
        if output_tsv_dir:
            df.to_csv(output_tsv_dir + "/" + sheetname.lower() + ".tsv", sep="\t", index=False)
        df.to_excel(writer, sheetname, index=False)


def write_mutation_summary(snps_high_moderate, snps_low_modifier,
                           snps_synonymous, snps_nonsynonymous,
                           indels_high_moderate,
                           indels_low_modifier,
                           indels_synonymous, indels_nonsynonymous,
                           hotspot,
                           excel_file,
                           absolute_somatic_txts,
                           absolute_segments,
                           output_tsv_dir,
                           annotation_tsv,
                           include_all,
                           summary_config):
    # create output tsv dir if required
    if output_tsv_dir:
        mkdir_p(output_tsv_dir)

    # create absolute df with cancer cell fractions
    if absolute_somatic_txts and absolute_segments:
        absdf = create_absolute_df(absolute_somatic_txts, absolute_segments)
    else:
        absdf = None
    # create annotation df
    if annotation_tsv:
        annotdf = pd.read_csv(annotation_tsv, sep="\t", encoding='utf-8')
    else:
        annotdf = None
    if summary_config:
        config = yaml.load(open(summary_config))
    else:
        config = None
    summary_columns = "CHROM,POS,TUMOR_SAMPLE,NORMAL_SAMPLE,ID,UPS_Coord,variantCaller,ANN[*].GENE,ANN[*].EFFECT,ANN[*].HGVS_P," \
        "SYMBOL,Variant_Classification,HGVSp_Short," \
        "TUMOR_MAF,NORMAL_MAF,TUMOR_DP,NORMAL_DP," \
        "AF,ExAC_AF,MutationTaster_pred,provean_pred,FATHMM_pred,parssnp_pred," \
        "fuentes,dgd,oncoKB_level,oncoKB_cancer_type,offTarget," \
        "facetsLOHCall,pathogenicity,HOTSPOT,HOTSPOT_INTERNAL,cmo_hotspot,clonalStatus,ccf".split(",")
    # find chasm score columns, they are prefixed with chosen classifier
    #chasm_score_columns = [c for c in pd.read_csv(snps_high_moderate, encoding='utf-8', sep="\t").columns if "chasm_score" in c]
    chasm_pred_columns = [c for c in pd.read_csv(snps_high_moderate, encoding='utf-8', sep="\t").columns if "chasm_pred" in c]
    # add gene annotations and chasm score columns
    summary_columns += chasm_pred_columns + "cancer_gene_census,kandoth,lawrence,num_cancer_gene,hap_insuf,REF,ALT,ANN[*].IMPACT".split(",")

    writer = pd.ExcelWriter(excel_file, options={'encoding':'utf-8'})
    writer.book.use_zip64()

    # merge mutation taster and provean columns
    def merge_ann_cols(df):
        if 'MutationTaster_pred' in df and 'MT_pred' in df:
            df.ix[df['MutationTaster_pred'] == '.', 'MutationTaster_pred'] = df.ix[df['MutationTaster_pred'] == '.', 'MT_pred']
            df.ix[df['MutationTaster_pred'].str.contains('disease').fillna(False), 'MutationTaster_pred'] = 'D'
            df.ix[df['MutationTaster_pred'].str.contains('poly').fillna(False), 'MutationTaster_pred'] = 'N'
        if 'dbNSFP_PROVEAN_pred' in df:
            df['provean_pred'] = df['dbNSFP_PROVEAN_pred']
        if 'provean_pred' in df:
            df['provean_pred'] = df['provean_pred'].fillna('Failed')
            df.ix[df['provean_pred'].str.contains('N').fillna(False), 'provean_pred'] = 'N'
            df.ix[df['provean_pred'].str.contains('D').fillna(False), 'provean_pred'] = 'D'
        return df

    def read_tsv(tsv):
        df = pd.read_csv(tsv, sep="\t", dtype={"CHROM": str})
        for col in df.select_dtypes(include=['object']):
            if len(df.index) > 0 and type(df.ix[0, col]).__name__ == 'str':
                df[col] = df[col].str.decode('unicode_escape').str.encode('ascii', 'ignore')
        return merge_ann_cols(df)

    # add summaries
    required_columns = summary_columns + "NORMAL.AD TUMOR.AD facetsLCN_EM".split()
    if include_all:
        mutsdf = pd.concat([add_non_existent_columns(select_annotations_with_impact(read_tsv(snps_high_moderate), "HIGH|MODERATE"), required_columns, ".")[required_columns],
                            add_non_existent_columns(select_annotations_with_impact(read_tsv(snps_low_modifier), "LOW|MODIFIER"), required_columns, ".")[required_columns],
                            add_non_existent_columns(select_annotations_with_impact(read_tsv(indels_high_moderate), "HIGH|MODERATE"), required_columns, ".")[required_columns]],
                            ignore_index=True).sort_values("TUMOR_SAMPLE CHROM POS".split())
    else:
        mutsdf = pd.concat([add_non_existent_columns(select_annotations_with_impact(read_tsv(snps_high_moderate), "HIGH|MODERATE", filter_effect='.*(sequence_feature|structural_interaction_variant|protein_protein_contact).*', config=config), required_columns, ".")[required_columns],
                            add_non_existent_columns(select_annotations_with_impact(read_tsv(snps_low_modifier), "LOW", select_effect=".*synonymous_variant.*", config=config), required_columns, ".")[required_columns],
                            add_non_existent_columns(select_annotations_with_impact(read_tsv(indels_high_moderate), "HIGH|MODERATE", filter_effect='.*(structural_interaction_variant|protein_protein_contact).*', config=config), required_columns, ".")[required_columns]],
                            ignore_index=True).sort_values("TUMOR_SAMPLE CHROM POS".split())
    #exac_af_sel = mutsdf["ExAC_AF"].apply(lambda x: x == "." or float(x) < max_exac_af)
    alldf = pd.concat([add_non_existent_columns(select_annotations_with_impact(read_tsv(snps_high_moderate), "HIGH|MODERATE"), required_columns, ".")[required_columns],
                        add_non_existent_columns(select_annotations_with_impact(read_tsv(snps_low_modifier), "LOW|MODIFIER"), required_columns, ".")[required_columns],
                        add_non_existent_columns(select_annotations_with_impact(read_tsv(indels_high_moderate), "HIGH|MODERATE"), required_columns, ".")[required_columns],
                        add_non_existent_columns(select_annotations_with_impact(read_tsv(indels_low_modifier), "LOW|MODIFIER"), required_columns, ".")[required_columns]],
                        ignore_index=True).sort_values("TUMOR_SAMPLE CHROM POS".split())
    add_columns_write_excel(alldf, writer, "ALL", absdf,
        write_columns=summary_columns, output_tsv_dir=output_tsv_dir,
        annotdf=annotdf, config=config)
    add_columns_write_excel(mutsdf, writer, "MUTATION_SUMMARY", absdf,
        write_columns=summary_columns, output_tsv_dir=output_tsv_dir,
        annotdf=annotdf, config=config)
    add_columns_write_excel(select_annotations_with_impact(read_tsv(snps_high_moderate), "HIGH|MODERATE", config=config),
        writer, "SNV_HIGH_MODERATE_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(snps_low_modifier), writer, "SNV_LOW_MODIFIER_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(snps_synonymous), writer, "SNV_SYNONYMOUS_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(select_annotations_with_impact(read_tsv(snps_nonsynonymous), "HIGH|MODERATE", config=config),
        writer, "SNV_NONSYNONYMOUS_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(select_annotations_with_impact(read_tsv(indels_high_moderate), "HIGH|MODERATE", config=config),
        writer, "INDEL_HIGH_MODERATE_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(indels_low_modifier), writer, "INDEL_LOW_MODIFIER_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(indels_synonymous), writer, "INDEL_SYNONYMOUS_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(select_annotations_with_impact(read_tsv(indels_nonsynonymous), "HIGH|MODERATE", config=config),
        writer, "INDEL_NONSYNONYMOUS_SUMMARY", absdf, write_columns=summary_columns, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)

    # add raw files both as excel and tsv
    if hotspot is not None:
        add_columns_write_excel(read_tsv(hotspot), writer, "hotspot", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(snps_high_moderate), writer, "snps_high_moderate", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(snps_low_modifier), writer, "snps_low_modifier", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(snps_synonymous), writer, "snps_synonymous", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(snps_nonsynonymous), writer, "snps_nonsynonymous", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(indels_high_moderate), writer, "indels_high_moderate", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(indels_low_modifier), writer, "indels_low_modifier", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(indels_synonymous), writer, "indels_synonymous", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)
    add_columns_write_excel(read_tsv(indels_nonsynonymous), writer, "indels_nonsynonymous", absdf, output_tsv_dir=output_tsv_dir, annotdf=annotdf, config=config)

    writer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("snps_high_moderate", type=str, help="TSV")
    parser.add_argument("snps_low_modifier", type=str, help="TSV")
    parser.add_argument("snps_synonymous", type=str, help="TSV")
    parser.add_argument("snps_nonsynonymous", type=str, help="TSV")
    parser.add_argument("indels_high_moderate", type=str, help="TSV")
    parser.add_argument("indels_low_modifier", type=str, help="TSV")
    parser.add_argument("indels_synonymous", type=str, help="TSV")
    parser.add_argument("indels_nonsynonymous", type=str, help="TSV")
    parser.add_argument("excel_file", type=str, help="mutation summary excel")
    parser.add_argument("--hotspot", type=str, help="hotspot table", default=None)
    parser.add_argument("--absolute_somatic_txts", default=None, type=str, help="TSV comma separated list of somatic files of absolute input")
    parser.add_argument("--absolute_segments", default=None, type=str, help="TSV comma separated list of absolute mutations output")
    parser.add_argument("--output_tsv_dir", default=None, type=str, help="Output raw sheets as tsv in given directory")
    parser.add_argument("--annotation_tsv", default=None, type=str, help="File with TUMOR_SAMPLE NORMAL_SAMPLE CHROM POS REF ALT, plus other columns of choice for annotation")
    #parser.add_argument("--max_exac_af", default=1, type=float, help="Set threshold for ExAC_AF column. Only applied to MUTATION_SUMMARY column.")
    parser.add_argument("--include_all", default=False, action='store_true',
                        help="include all mutations in the complete summary")
    parser.add_argument("--summary_config", default=None, type=str,
        help="Summary config yaml for summary/plotting options")
    args = parser.parse_args()
    if args.absolute_somatic_txts and args.absolute_segments:
        absolute_somatic_txts = args.absolute_somatic_txts.split(",")
        absolute_segments = args.absolute_segments.split(",")
        if not (len(absolute_somatic_txts) == len(absolute_segments)):
            raise Exception
    else:
        absolute_somatic_txts = None
        absolute_segments = None
    write_mutation_summary(args.snps_high_moderate,
                           args.snps_low_modifier,
                           args.snps_synonymous,
                           args.snps_nonsynonymous,
                           args.indels_high_moderate,
                           args.indels_low_modifier,
                           args.indels_synonymous,
                           args.indels_nonsynonymous,
                           args.hotspot,
                           args.excel_file,
                           absolute_somatic_txts,
                           absolute_segments,
                           args.output_tsv_dir,
                           args.annotation_tsv,
                           args.include_all,
                           args.summary_config)

if __name__ == "__main__":
    main()
